// Static validation and opt-in quiescence probe; no trainer or parameter writer.
#include <cstddef>
#include <cerrno>
#include <cstdlib>
#include <limits>
#include <cstdio>
#include <cstring>
#include <iostream>
#include <iomanip>
#include <map>
#include <regex>
#include <sstream>
#include <string>
#include "bitboard.h"
#include "evaluation.h"
#include "extended_board.h"
#include "huffman_code.h"
#include "material.h"
#include "mate1ply.h"
#include "node.h"
#include "progress.h"
#include "search.h"
#include "movegen.h"
#include "psq.h"
#include "square.h"
#include "teacher_data.h"
#include "zobrist.h"

namespace {

std::string Key(const Position& pos) {
  const std::string sfen = pos.ToSfen();
  return sfen.substr(0, sfen.find_last_of(' '));
}

bool LoadParams(const char* path) {
  std::FILE* fp = std::fopen(path, "rb");
  if (!fp) return false;
  const bool ok = std::fread(g_eval_params.get(), sizeof(EvalParameters), 1, fp) == 1
      && std::fgetc(fp) == EOF && !std::ferror(fp);
  std::fclose(fp);
  if (ok) Material::Init();
  return ok;
}

bool LoadProgress(const char* path) {
  std::FILE* fp = std::fopen(path, "rb");
  if (!fp) return false;
  const bool ok = std::fread(&Progress::weights, sizeof(Progress::weights), 1, fp) == 1
      && std::fgetc(fp) == EOF && !std::ferror(fp);
  std::fclose(fp);
  if (!ok) return false;
  for (Square sq : Square::all_squares())
    for (PsqIndex i : PsqIndex::all_indices())
      if (g_eval_params->king_piece[sq][i][3] != Progress::weights[sq][i]) return false;
  return true;
}

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
  *move = Move::FromSfen(token, pos);
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

void PrintParts(std::ostringstream& out, const EvalDetail& detail) {
  const PackedScore kp = detail.kp[kBlack] + detail.kp[kWhite] + detail.king_preference;
  const PackedScore others = detail.controls + detail.two_pieces + detail.king_safety + detail.sliders;
  out << "{\"kp\":[";
  for (int i = 0; i < 4; ++i) { if (i) out << ','; out << kp[i]; }
  out << "],\"others\":[";
  for (int i = 0; i < 4; ++i) { if (i) out << ','; out << others[i]; }
  out << "],\"tempo\":[";
  for (int i = 0; i < 4; ++i) { if (i) out << ','; out << g_eval_params->tempo[i]; }
  out << "]}";
}

bool PerturbTempo(char** values) {
  int32_t changed[3];
  for (int i = 0; i < 3; ++i) {
    char* end = nullptr;
    errno = 0;
    const long long inc = std::strtoll(values[i], &end, 10);
    if (errno || end == values[i] || *end || inc < -5LL*kFvScale || inc > 5LL*kFvScale)
      return false;
    const int64_t value = int64_t(g_eval_params->tempo[i]) + inc;
    if (value < std::numeric_limits<int32_t>::min() || value > std::numeric_limits<int32_t>::max())
      return false;
    changed[i] = static_cast<int32_t>(value);
  }
  // Only three tempo entries in this process's private memory are changed.
  for (int i = 0; i < 3; ++i) g_eval_params->tempo[i] = changed[i];
  return true;
}

void Quiescence(const std::string& line) {
  Position pos = Position::CreateStartPosition();
  std::istringstream input(line);
  std::string token;
  int ply = 0;
  while (input >> token) {
    Move move = kMoveNone;
    if (++ply > 600 || !LegalToken(token, pos, &move)) {
      std::cout << "{\"ok\":false,\"error\":\"illegal_root_history\"}\n";
      return;
    }
    pos.MakeMove(move);
  }
  Evaluation::SetShinYonenagaGyoku(true);
  // Match RootStrap's compressed-position boundary, which omits game history.
  Node node(HuffmanCode::DecodePosition(HuffmanCode::EncodePosition(pos)));
  std::unique_ptr<SharedData> shared(new SharedData);
  shared->hash_table.SetSize(1);
  shared->Clear();
  std::unique_ptr<Search> search(new Search(*shared));
  search->set_learning_mode(true);  // No TT score substitution or hash cut.
  search->PrepareForNextSearch();
  const Score score = search->AlphaBetaSearch(node, -kScoreKnownWin, kScoreKnownWin, kDepthZero);
  const std::vector<Move> pv(search->pv_table().begin(), search->pv_table().end());
  std::ostringstream out;
  out << "{\"ok\":true,\"qscore\":" << score << ",\"nodes\":" << search->num_nodes_searched()
      << ",\"root_sfen\":\"" << Key(node) << " 1\",\"root_side\":\""
      << (node.side_to_move() == kBlack ? "black" : "white") << "\",\"pv\":[";
  for (size_t i = 0; i < pv.size(); ++i) {
    if (i) out << ',';
    out << '"' << pv[i].ToSfen() << '"';
  }
  out << ']';
  for (Move move : pv) {
    if (!node.MoveIsLegal(move)) {
      std::cout << "{\"ok\":false,\"error\":\"illegal_qsearch_pv\"}\n";
      return;
    }
    node.Evaluate();
    node.MakeMove(move);
  }
  double progress = 0.0;
  const int cached = node.Evaluate(&progress);
  const EvalDetail full = Evaluation::EvaluateAll(node, PsqList(node));
  const int scratch = full.ComputeFinalScore(node.side_to_move());
  Score repetition = kScoreNone;
  const bool repeats = node.DetectRepetition(&repetition);
  out << ",\"leaf_sfen\":\"" << Key(node) << " 1\",\"leaf_side\":\""
      << (node.side_to_move() == kBlack ? "black" : "white")
      << "\",\"leaf_eval_cached\":" << cached << ",\"leaf_eval_full\":" << scratch
      << ",\"leaf_progress\":" << std::setprecision(17) << progress
      << ",\"leaf_repetition\":" << (repeats ? "true" : "false")
      << ",\"leaf_in_check\":" << (node.in_check() ? "true" : "false")
      << ",\"leaf_parts\":";
  PrintParts(out, full);
  out << '}';
  std::cout << out.str() << '\n';
}

void Replay(const std::string& line, bool evaluate, bool details) {
  Position pos = Position::CreateStartPosition();
  std::map<std::string, int> seen;
  std::ostringstream out;
  std::istringstream input(line);
  std::string token;
  int ply = 0;
  out << "{\"ok\":true,\"positions\":[";
  for (;;) {
    const std::string key = Key(pos);
    const HuffmanCode code = HuffmanCode::EncodePosition(pos);
    if (HuffmanCode::DecodePosition(code) != pos) {
      std::cout << "{\"ok\":false,\"error\":\"huffman_roundtrip\",\"ply\":" << ply << "}\n";
      return;
    }
    char hex[65];
    const unsigned char* bytes = reinterpret_cast<const unsigned char*>(&code);
    for (int i = 0; i < 32; ++i) std::snprintf(hex + 2*i, 3, "%02x", bytes[i]);
    if (ply) out << ',';
    out << "{\"sfen\":\"" << key << " 1\",\"occurrences\":" << ++seen[key]
        << ",\"huffman_hex\":\"" << hex << "\"";
    if (evaluate) {
      Evaluation::SetShinYonenagaGyoku(true);
      double progress = 0.0;
      const EvalDetail on_detail = Evaluation::EvaluateAll(pos, PsqList(pos));
      const int on = on_detail.ComputeFinalScore(
          pos.side_to_move(), &progress);
      Evaluation::SetShinYonenagaGyoku(false);
      const EvalDetail off_detail = Evaluation::EvaluateAll(pos, PsqList(pos));
      const int off = off_detail.ComputeFinalScore(pos.side_to_move());
      out << ",\"eval_on\":" << on << ",\"eval_off\":" << off
          << ",\"progress\":" << std::setprecision(17) << progress;
      if (details) {
        out << ",\"on_parts\":"; PrintParts(out, on_detail);
        out << ",\"off_parts\":"; PrintParts(out, off_detail);
      }
    }
    out << '}';
    if (!(input >> token)) break;
    Move move = kMoveNone;
    if (ply >= 600 || !LegalToken(token, pos, &move)) {
      std::cout << "{\"ok\":false,\"error\":\"illegal_move\",\"ply\":" << ply+1 << "}\n";
      return;
    }
    pos.MakeMove(move);
    ++ply;
  }
  out << "]}";
  std::cout << out.str() << '\n';
}

}  // namespace

int main(int argc, char** argv) {
  if (argc == 2 && std::string(argv[1]) == "--layout") {
    std::cout << "{\"eval_parameters_bytes\":" << sizeof(EvalParameters)
        << ",\"tempo_offset\":" << offsetof(EvalParameters, tempo)
        << ",\"packed_score_bytes\":" << sizeof(PackedScore)
        << ",\"teacher_position_bytes\":" << sizeof(TeacherPosition)
        << ",\"teacher_move_offset\":" << offsetof(TeacherPosition, move)
        << ",\"teacher_score_offset\":" << offsetof(TeacherPosition, score)
        << ",\"fv_scale\":" << kFvScale << "}\n";
    return 0;
  }
  const bool perturb = argc == 6 && std::string(argv[1]) == "--perturb-tempo";
  const bool qsearch = argc == 4 && std::string(argv[1]) == "--qsearch";
  const bool details = perturb || (argc == 3 && std::string(argv[1]) == "--evaluate-details");
  const bool evaluate = details || (argc == 3 && std::string(argv[1]) == "--evaluate");
  const bool inspect = argc == 3 && std::string(argv[1]) == "--inspect-params";
  if (!evaluate && !inspect && !qsearch && !(argc == 2 && std::string(argv[1]) == "--replay")) return 2;
  Square::Init();
  Bitboard::Init();
  ExtendedBoard::Init();
  HuffmanCode::Init();
  PsqPair::Init();
  if ((evaluate || inspect || qsearch) && !LoadParams(argv[2])) {
    std::cerr << "Invalid parameter file size or read failure\n";
    return 2;
  }
  if (qsearch) {
    if (!LoadProgress(argv[3])) {
      std::cerr << "Progress data size/weights do not match params\n";
      return 2;
    }
    Zobrist::Init();
    InitMateInOnePly();
    Search::Init();
  }
  if (perturb && !PerturbTempo(argv+3)) {
    std::cerr << "Invalid raw tempo increment (maximum 5cp per coefficient)\n";
    return 2;
  }
  if (inspect) {
    std::cout << "{\"tempo_raw\":[";
    for (int i = 0; i < 4; ++i) {
      if (i) std::cout << ',';
      std::cout << g_eval_params->tempo[i];
    }
    std::cout << "],\"fv_scale\":" << kFvScale << "}\n";
    return 0;
  }
  for (std::string line; std::getline(std::cin, line);) {
    if (qsearch) Quiescence(line);
    else Replay(line, evaluate, details);
    std::cout.flush();
  }
}
