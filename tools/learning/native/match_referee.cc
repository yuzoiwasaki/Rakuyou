// Standalone match adjudication; no evaluation, search, or runtime data access.
#include <iostream>
#include <map>
#include <regex>
#include <set>
#include <sstream>
#include <string>
#include <vector>
#include "position.h"
#include "movegen.h"
#include "extended_board.h"
#include "zobrist.h"
namespace {
bool LegalToken(const std::string& token, const Position& pos, Move* move) {
  static const std::regex syntax("([1-9][a-i][1-9][a-i]\\+?|[PLNSGBR]\\*[1-9][a-i])");
  if (!std::regex_match(token, syntax)) return false;
  const bool drop = token[1] == '*';
  if (!drop) {
    const Piece piece = pos.piece_on(Square::FromSfen(token.substr(0, 2)));
    if (piece == kNoPiece || piece.color() != pos.side_to_move()) return false;
    const Piece target = pos.piece_on(Square::FromSfen(token.substr(2, 2)));
    if (target != kNoPiece && target.type() == kKing) return false;
    if (piece.type() == kKnight && token.size() == 4 &&
        relative_rank(pos.side_to_move(), Square::FromSfen(token.substr(2, 2)).rank()) <= kRank2)
      return false;
  }
  // FromSfen uses asserting constructors. A syntactically valid candidate
  // (including a generated underpromotion) can still be structurally illegal.
  // Construct unchecked, then reject it through IsOk before MoveIsLegal.
  const Square to = Square::FromSfen(token.substr(2, 2));
  if (drop) {
    const Piece piece(pos.side_to_move(), Piece::FromSfen(token.substr(0, 1)).type());
    *move = Move::Create(piece, to);
  } else {
    const Square from = Square::FromSfen(token.substr(0, 2));
    *move = Move::Create(pos.piece_on(from), from, to, token.size() == 5,
                         pos.piece_on(to));
  }
  if (!move->IsOk() || !pos.MoveIsLegal(*move)) return false;
  if (drop) {
    const Rank rank = relative_rank(pos.side_to_move(), move->to().rank());
    if ((move->piece_type() == kPawn || move->piece_type() == kLance) && rank == kRank1)
      return false;
    if (move->piece_type() == kKnight && rank <= kRank2) return false;
    // Position::MoveIsLegal alone does not reject a mating pawn drop.
    if (move->is_pawn_drop()) {
      Position child(pos);
      child.MakeMove(*move);
      if (child.in_check() && SimpleMoveList<kAllMoves, true>(child).size() == 0)
        return false;
    }
  }
  return true;
}


struct Snapshot { Color side; bool check; };
void Replay(const std::string& line, const std::string& initial) {
  Position pos = initial.empty() ? Position::CreateStartPosition() : Position::FromSfen(initial);
  std::map<std::string, std::vector<size_t> > seen;
  std::vector<Snapshot> history;
  std::ostringstream out;
  std::string result = "ongoing", reason;
  std::istringstream input(line);
  std::string token;
  size_t ply = 0;
  out << "{\"ok\":true,\"positions\":[";
  for (;;) {
    const std::string sfen = pos.ToSfen();
    const std::string key = sfen.substr(0, sfen.find_last_of(' '));
    std::vector<size_t>& occurrences = seen[key];
    occurrences.push_back(ply);
    history.push_back(Snapshot{pos.side_to_move(), pos.in_check()});
    std::set<std::string> legal_tokens;
    for (const auto& candidate : SimpleMoveList<kAllMoves, true>(pos)) {
      Move checked = kMoveNone;
      std::string token = candidate.move.ToSfen();
      if (LegalToken(token, pos, &checked)) legal_tokens.insert(token);
      // Search move generation suppresses some legal underpromotions.
      if (token.back() == '+') {
        token.pop_back();
        if (LegalToken(token, pos, &checked)) legal_tokens.insert(token);
      }
    }
    const int legal_count = static_cast<int>(legal_tokens.size());
    if (ply) out << ',';
    out << "{\"sfen\":\"" << sfen << "\",\"occurrences\":" << occurrences.size()
        << ",\"in_check\":" << (pos.in_check() ? "true" : "false")
        << ",\"side\":\"" << (pos.side_to_move() == kBlack ? "black" : "white")
        << "\",\"can_declare\":" << (pos.WinDeclarationIsPossible(true) ? "true" : "false")
        << ",\"legal_moves\":" << legal_count << '}';
    if (occurrences.size() == 4) {
      bool continuous[2] = {true, true};
      bool moved[2] = {false, false};
      for (size_t i = occurrences.front() + 1; i <= ply; ++i) {
        const Color mover = history[i-1].side;
        moved[mover] = true;
        continuous[mover] = continuous[mover] && history[i].check;
      }
      const bool black = continuous[kBlack] && moved[kBlack];
      const bool white = continuous[kWhite] && moved[kWhite];
      if (black && white) {
        std::cout << "{\"ok\":false,\"error\":\"ambiguous_perpetual_check\"}\n"; return;
      }
      result = black ? "white_win" : white ? "black_win" : "draw";
      reason = black || white ? "perpetual_check" : "repetition";
    } else if (!legal_count) {
      result = pos.side_to_move() == kBlack ? "white_win" : "black_win";
      reason = pos.in_check() ? "checkmate" : "no_legal_moves";
    }
    if (!(input >> token)) break;
    if (result != "ongoing") {
      std::cout << "{\"ok\":false,\"error\":\"history_after_terminal\"}\n"; return;
    }
    Move move = kMoveNone;
    if (++ply > 600 || !LegalToken(token, pos, &move)) {
      std::cout << "{\"ok\":false,\"error\":\"illegal_history\"}\n"; return;
    }
    pos.MakeMove(move);
  }
  out << "],\"result\":\"" << result << "\",\"reason\":";
  if (reason.empty()) out << "null"; else out << '\"' << reason << '\"';
  std::cout << out.str() << "}\n";
}
}
int main(int argc, char** argv) {
  std::string initial;
  if (argc == 3 && std::string(argv[1]) == "--sfen") initial = argv[2];
  else if (!(argc == 2 && std::string(argv[1]) == "--replay")) return 2;
  Square::Init(); Bitboard::Init(); ExtendedBoard::Init(); Zobrist::Init();
  for (std::string line; std::getline(std::cin, line);) { Replay(line, initial); std::cout.flush(); }
}
