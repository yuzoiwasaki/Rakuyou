#include "shin_book.h"

#include <fstream>
#include <sstream>
#include "synced_printf.h"

namespace {

bool IsUsiMove(const std::string& move) {
  if (move.size() != 4 && move.size() != 5) return false;
  if (move.size() == 5 && move[4] != '+') return false;
  if (move[1] == '*') {
    return move.size() == 4 && std::string("PLNSGBR").find(move[0]) != std::string::npos
        && move[2] >= '1' && move[2] <= '9'
        && move[3] >= 'a' && move[3] <= 'i';
  }
  return move[0] >= '1' && move[0] <= '9'
      && move[1] >= 'a' && move[1] <= 'i'
      && move[2] >= '1' && move[2] <= '9'
      && move[3] >= 'a' && move[3] <= 'i';
}

bool HasMovingPiece(const Position& position, const std::string& move) {
  if (move[1] == '*') return true;
  Piece piece = position.piece_on(Square::FromSfen(move.substr(0, 2)));
  return piece != kNoPiece && piece.color() == position.side_to_move();
}

}  // namespace

void ShinBook::ReadFromFile(const std::string& file_name) {
  entries_.clear();
  if (file_name.empty()) return;

  std::ifstream input(file_name);
  if (!input) {
    SYNCED_PRINTF("info string Failed to open ShinBookFile: %s\n", file_name.c_str());
    return;
  }

  std::string line;
  int line_number = 0;
  while (std::getline(input, line)) {
    ++line_number;
    if (line.empty() || line[0] == '#') continue;

    std::istringstream tokens(line);
    std::string token;
    Position position = Position::CreateStartPosition();
    bool valid = true;
    bool delimiter = false;
    while (tokens >> token) {
      if (token == "|") {
        delimiter = true;
        break;
      }
      if (!IsUsiMove(token)) { valid = false; break; }
      if (!HasMovingPiece(position, token)) { valid = false; break; }
      Move move = Move::FromSfen(token, position);
      if (!position.MoveIsLegal(move)) { valid = false; break; }
      position.MakeMove(move);
    }
    std::string book_move, extra;
    if (!valid || !delimiter || !(tokens >> book_move) || (tokens >> extra)
        || !IsUsiMove(book_move)) {
      SYNCED_PRINTF("info string Invalid ShinBookFile line %d\n", line_number);
      continue;
    }
    if (!HasMovingPiece(position, book_move)) {
      SYNCED_PRINTF("info string Illegal ShinBookFile line %d\n", line_number);
      continue;
    }
    Move move = Move::FromSfen(book_move, position);
    if (!position.MoveIsLegal(move)) {
      SYNCED_PRINTF("info string Illegal ShinBookFile line %d\n", line_number);
      continue;
    }
    bool duplicate = false;
    for (const Entry& entry : entries_) {
      if (entry.position == position) { duplicate = true; break; }
    }
    if (duplicate) {
      SYNCED_PRINTF("info string Duplicate ShinBookFile line %d\n", line_number);
      continue;
    }
    entries_.push_back({position, move});
  }
  SYNCED_PRINTF("info string ShinBookFile loaded %zu positions\n", entries_.size());
}

Move ShinBook::Probe(const Position& position) const {
  // Position equality includes the side to move, so Black and White entries
  // can share the format without borrowing the other side's moves.
  for (const Entry& entry : entries_) {
    if (entry.position == position) return entry.move;
  }
  return kMoveNone;
}
