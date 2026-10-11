// Search-free validation helper for Rakuyou learning-data preparation.
// Uses the Gikou position, move and Huffman implementations without a trainer.
#include <cstddef>
#include <cstdio>
#include <cstring>
#include <iostream>
#include <map>
#include <regex>
#include <sstream>
#include <string>
#include "bitboard.h"
#include "evaluation.h"
#include "extended_board.h"
#include "huffman_code.h"
#include "material.h"
#include "movegen.h"
#include "psq.h"
#include "square.h"
#include "teacher_data.h"

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

bool LegalToken(const std::string& token, const Position& pos, Move* move) {
  static const std::regex syntax("([1-9][a-i][1-9][a-i]\\+?|[PLNSGBR]\\*[1-9][a-i])");
  if (!std::regex_match(token, syntax)) return false;
  const bool drop = token[1] == '*';
  if (!drop) {
    const Piece piece = pos.piece_on(Square::FromSfen(token.substr(0, 2)));
    if (piece == kNoPiece || piece.color() != pos.side_to_move()) return false;
    const Piece target = pos.piece_on(Square::FromSfen(token.substr(2, 2)));
    if (target != kNoPiece && target.type() == kKing) return false;
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

void Replay(const std::string& line, bool evaluate) {
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
      const int on = Evaluation::Evaluate(pos);
      Evaluation::SetShinYonenagaGyoku(false);
      const int off = Evaluation::Evaluate(pos);
      out << ",\"eval_on\":" << on << ",\"eval_off\":" << off;
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
  const bool evaluate = argc == 3 && std::string(argv[1]) == "--evaluate";
  if (!evaluate && !(argc == 2 && std::string(argv[1]) == "--replay")) return 2;
  Square::Init();
  Bitboard::Init();
  ExtendedBoard::Init();
  HuffmanCode::Init();
  PsqPair::Init();
  if (evaluate && !LoadParams(argv[2])) {
    std::cerr << "Invalid parameter file size or read failure\n";
    return 2;
  }
  for (std::string line; std::getline(std::cin, line);) {
    Replay(line, evaluate);
    std::cout.flush();
  }
}
