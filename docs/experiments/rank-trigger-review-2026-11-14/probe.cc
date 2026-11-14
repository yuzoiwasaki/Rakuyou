// Bounded native audit of the isolated king-contact deficit term; no search.
#ifdef NDEBUG
#error "Build the probe with assertions enabled."
#endif
#define main LegacyLearningProbeMain
#include "../../../tools/learning/native/learning_data_probe.cc"
#undef main

#include <vector>
#include "rank_commitment.h"

namespace {
struct Contact {
  Square square;
  int attackers;
  int defenders;
  int deficit;
};

template<Color kColor>
std::vector<Contact> ProbeContacts(const Position& pos) {
  const Square king = pos.king_square(kColor);
  std::vector<Contact> contacts;
  for (int df = -1; df <= 1; ++df) {
    const int file = static_cast<int>(king.file()) + df;
    if (file < 0 || file >= 9) continue;
    for (int dr = -1; dr <= 1; ++dr) {
      const int rank = static_cast<int>(king.rank()) + dr;
      if ((df == 0 && dr == 0) || rank < 0 || rank >= 9) continue;
      const Square square(static_cast<File>(file), static_cast<Rank>(rank));
      const int a = std::min(3, pos.num_controls(~kColor, square));
      const int d = std::min(3, std::max(0, pos.num_controls(kColor, square) - 1));
      contacts.push_back(Contact{square, a, d, std::max(0, a - d)});
    }
  }
  return contacts;
}

template<Color kColor>
int ProbeDeficit(const Position& pos) {
  int total = 0;
  for (const Contact& item : ProbeContacts<kColor>(pos)) total += item.deficit;
  return total;
}

void PrintContacts(std::ostringstream& output, const std::vector<Contact>& contacts) {
  output << '[';
  for (size_t i = 0; i < contacts.size(); ++i) {
    if (i) output << ',';
    const Contact& item = contacts[i];
    output << "{\"square\":\"" << item.square.ToSfen() << "\",\"a\":"
           << item.attackers << ",\"d\":" << item.defenders
           << ",\"deficit\":" << item.deficit << '}';
  }
  output << ']';
}

void PrintSquares(std::ostringstream& output, Bitboard bb) {
  output << '['; bool first=true;
  while(bb.any()) {if(!first) output << ',';first=false;output << '"' << bb.pop_first_one().ToSfen() << '"';}
  output << ']';
}
template<Color side>
void PrintRankWitness(std::ostringstream& output,const Position& pos) {
  Square pawn;int attackers=0,defenders=0;
  if(!RankOvercommitment<side>(pos,&pawn,&attackers,&defenders)) {output << "null";return;}
  output << "{\"pawn\":\"" << pawn.ToSfen() << "\",\"attacker_count\":" << attackers << ",\"defender_count\":" << defenders << ",\"attackers\":";
  PrintSquares(output,RankParticipants(pos,pawn,~side));output << ",\"defenders\":";
  PrintSquares(output,RankParticipants(pos,pawn,side));output << ",\"direct_attackers\":";
  PrintSquares(output,pos.AttackersTo(pawn,pos.pieces(),~side));output << '}';
}

void Check(Node& node) {
  const EvalDetail detail = Evaluation::EvaluateAll(node, PsqList(node));
  assert(detail.ComputeFinalScore(node.side_to_move()) == node.Evaluate());
  Position flipped(node);
  flipped.Flip();
  assert(RankOvercommitment<kBlack>(node)==RankOvercommitment<kWhite>(flipped));
  assert(RankOvercommitment<kWhite>(node)==RankOvercommitment<kBlack>(flipped));
  assert(ProbeDeficit<kBlack>(node) == ProbeDeficit<kWhite>(flipped));
  assert(ProbeDeficit<kWhite>(node) == ProbeDeficit<kBlack>(flipped));
}

void Inspect(const std::string& line) {
  const bool sfen = line.compare(0, 5, "sfen ") == 0;
  const bool moves = line.compare(0, 6, "moves ") == 0 || line == "moves";
  if (!sfen && !moves) {
    std::cout << "{\"ok\":false,\"error\":\"input\"}\n";
    return;
  }
  Node node(sfen ? Position::FromSfen(line.substr(5)) : Position::CreateStartPosition());
  std::vector<Move> history;
  Check(node);
  if (moves) {
    std::istringstream input(line.substr(line == "moves" ? 5 : 6));
    std::string token;
    while (input >> token) {
      Move move = kMoveNone;
      if (history.size() >= 600 || !LegalToken(token, node, &move)) {
        std::cout << "{\"ok\":false,\"error\":\"illegal_history\"}\n";
        return;
      }
      node.MakeMove(move);
      history.push_back(move);
      Check(node);
    }
  }
  const EvalDetail detail = Evaluation::EvaluateAll(node, PsqList(node));
  const std::vector<Contact> black_contacts = ProbeContacts<kBlack>(node);
  const std::vector<Contact> white_contacts = ProbeContacts<kWhite>(node);
  int black = 0, white = 0;
  for (const Contact& item : black_contacts) black += item.deficit;
  for (const Contact& item : white_contacts) white += item.deficit;
  double progress = 0;
  const int score = detail.ComputeFinalScore(node.side_to_move(), &progress);
  std::ostringstream output;
  output << "{\"ok\":true,\"sfen\":\"" << node.ToSfen()
         << "\",\"ply\":" << history.size()
         << ",\"score\":" << score << ",\"progress\":"
         << std::setprecision(17) << progress << ",\"d_black\":" << black
         << ",\"d_white\":" << white << ",\"contacts_black\":";
  PrintContacts(output, black_contacts);
  output << ",\"contacts_white\":";
  PrintContacts(output, white_contacts);
  output << ",\"rank_black\":" << int(RankOvercommitment<kBlack>(node))
         << ",\"rank_white\":" << int(RankOvercommitment<kWhite>(node));
  output << ",\"witness_black\":";PrintRankWitness<kBlack>(output,node);
  output << ",\"witness_white\":";PrintRankWitness<kWhite>(output,node);
  output << ",\"king_safety\":[";
  for (int i = 0; i < 4; ++i) {
    if (i) output << ',';
    output << detail.king_safety[i];
  }
  output << "],\"support_chain\":[";
  for (int i = 0; i < 4; ++i) {
    if (i) output << ',';
    output << detail.support_chain[i];
  }
  output << "],\"parts\":";
  PrintParts(output, detail);
  output << '}';
  for (auto it = history.rbegin(); it != history.rend(); ++it) {
    node.UnmakeMove(*it);
    Check(node);
  }
  std::cout << output.str() << '\n';
}
}  // namespace

int main(int argc, char** argv) {
  if (argc != 4) return 2;
  Square::Init();
  Bitboard::Init();
  ExtendedBoard::Init();
  Zobrist::Init();
  HuffmanCode::Init();
  PsqPair::Init();
  if (!LoadParams(argv[1])) return 2;
  Evaluation::SetShinYonenagaGyoku(true);
  Evaluation::SetSupportChainBonus(std::atoi(argv[2]));
  Evaluation::SetKingContactDeficitBonus(std::atoi(argv[3]));
  for (std::string line; std::getline(std::cin, line);) {
    Inspect(line);
    std::cout.flush();
  }
}
