// Offline diagnostic only: legal entries and immediate legal captures, with SEE.
#ifdef NDEBUG
#error "Assertions required"
#endif
#include <cassert>
#include <cmath>
#include <iostream>
#include <sstream>
#include <vector>
#include "bitboard.h"
#include "evaluation.h"
#include "extended_board.h"
#include "material.h"
#include "movegen.h"
#include "position.h"
#include "psq.h"
#include "swap.h"
#include "zobrist.h"

// The engine's basic legal list does not itself exclude pawn-drop mate.
bool PawnDropMate(Position& pos, Move move) {
  if (!move.is_pawn_drop()) return false;
  pos.MakeMove(move);
  const bool mate = pos.in_check() && SimpleMoveList<kAllMoves, true>(pos).empty();
  pos.UnmakeMove(move);
  return mate;
}

int main(int argc, char** argv) {
  if (argc != 2) return 2;
  Square::Init(); Bitboard::Init(); ExtendedBoard::Init(); Zobrist::Init(); PsqPair::Init();
  Evaluation::ReadParametersFromFile(argv[1]); Material::Init();
  int index = 0;
  for (std::string line; std::getline(std::cin, line); ++index) {
    const bool sfen = line.compare(0, 5, "sfen ") == 0;
    if (!sfen && line.compare(0, 6, "moves ") != 0) return 2;
    Position pos = sfen ? Position::FromSfen(line.substr(5)) : Position::CreateStartPosition();
    if (!sfen) {
      std::istringstream input(line.substr(6));
      for (std::string token; input >> token;) {
        const Move move = Move::FromSfen(token, pos);
        assert(move.IsOk() && pos.MoveIsLegal(move) && !PawnDropMate(pos, move));
        pos.MakeMove(move);
      }
    }
    const std::string original = pos.ToSfen();
    const Color defender = ~pos.side_to_move();
    assert(pos.king_exists(defender));
    const Square king = pos.king_square(defender);
    const int forward = defender == kBlack ? -1 : 1;
    for (ExtMove ext : SimpleMoveList<kAllMoves, true>(pos)) {
      const Move entry = ext.move;
      const int distance = (int(entry.to().rank()) - int(king.rank())) * forward;
      if (distance < 1 || distance > 3 || std::abs(int(entry.to().file()) - int(king.file())) > 2) continue;
      if (PawnDropMate(pos, entry)) continue;
      const int see = Swap::Evaluate(entry, pos);
      pos.MakeMove(entry);
      std::vector<std::pair<Move, int>> captures;
      for (ExtMove reply : SimpleMoveList<kAllMoves, true>(pos)) {
        if (reply.move.is_capture() && reply.move.to() == entry.to()) {
          assert(pos.MoveIsLegal(reply.move));
          captures.emplace_back(reply.move, Swap::Evaluate(reply.move, pos));
        }
      }
      std::cout << index << ' ' << entry.ToSfen() << ' ' << see << ' '
                << pos.in_check() << ' ' << distance;
      for (const auto& reply : captures) std::cout << ' ' << reply.first.ToSfen() << ':' << reply.second;
      std::cout << '\n';
      pos.UnmakeMove(entry);
      assert(pos.ToSfen() == original);
    }
  }
}
