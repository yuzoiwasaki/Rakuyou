// Offline classification prototype. No effect on engine evaluation or search.
#ifdef NDEBUG
#error "Assertions required"
#endif
#include <cassert>
#include <cmath>
#include <iostream>
#include <sstream>
#include "bitboard.h"
#include "evaluation.h"
#include "extended_board.h"
#include "material.h"
#include "movegen.h"
#include "position.h"
#include "psq.h"
#include "swap.h"
#include "zobrist.h"

bool PawnDropMate(Position& pos, Move move) {
  if (!move.is_pawn_drop()) return false;
  pos.MakeMove(move);
  const bool mate = pos.in_check() && SimpleMoveList<kAllMoves, true>(pos).empty();
  pos.UnmakeMove(move);
  return mate;
}

// Targets of legal, non-losing captures if the side could move now.
Bitboard CaptureTargets(const Position& pos) {
  Bitboard targets;
  for (ExtMove ext : SimpleMoveList<kAllMoves, true>(pos)) {
    if (ext.move.is_capture() && Swap::Evaluate(ext.move, pos) >= 0) targets.set(ext.move.to());
  }
  return targets;
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
      std::istringstream in(line.substr(6));
      for (std::string token; in >> token;) {
        const Move move = Move::FromSfen(token, pos);
        assert(move.IsOk() && pos.MoveIsLegal(move) && !PawnDropMate(pos, move));
        pos.MakeMove(move);
      }
    }
    const std::string original = pos.ToSfen();
    const Color side = pos.side_to_move();
    assert(pos.king_exists(side));
    const Square king = pos.king_square(side);
    const int forward = side == kBlack ? -1 : 1;
    const Bitboard before_targets = CaptureTargets(pos);
    for (ExtMove ext : SimpleMoveList<kAllMoves, true>(pos)) {
      const Move move = ext.move;
      if (PawnDropMate(pos, move)) continue;
      const bool forced = pos.in_check();
      const bool tactical = move.is_capture_or_promotion() || pos.MoveGivesCheck(move);
      bool blockade = false, exposed = false;
      Bitboard new_links, new_targets;
      if (!forced && !tactical && move.piece_type() != kKing) {
        const int distance = (int(move.to().rank())-int(king.rank()))*forward;
        const bool nearby = std::abs(int(move.to().file())-int(king.file())) <= 2
                         && std::abs(int(move.to().rank())-int(king.rank())) <= 2;
        const bool contested_hole = nearby && distance >= 1 && distance <= 2
              && pos.piece_on(move.to()).is(kNoPieceType)
              && pos.num_controls(~side, move.to()) > 0;
        Bitboard old_links;
        const bool guard = move.piece_type() == kGold || move.piece_type() == kSilver;
        if (guard && !move.is_drop()) {
          old_links = step_attacks_bb(move.piece(), move.from()) & pos.pieces(side, kGold, kSilver);
        }
        pos.MakeMove(move);
        blockade = contested_hole && pos.num_controls(side, move.to()) > 0
                 && pos.num_controls(side, move.to()) >= pos.num_controls(~side, move.to());
        if (guard && nearby) {
          Bitboard links = step_attacks_bb(pos.piece_on(move.to()), move.to())
                         & pos.pieces(side, kGold, kSilver) & ~old_links;
          while (links.any()) {
            const Square target = links.pop_first_one();
            const int advance = (int(target.rank())-int(king.rank()))*forward;
            if (advance >= 1 && advance <= 2
                && std::abs(int(target.file())-int(king.file())) <= 2) new_links.set(target);
          }
        }
        for (ExtMove reply : SimpleMoveList<kAllMoves, true>(pos)) {
          if (reply.move.is_capture() && reply.move.to() == move.to()
              && Swap::Evaluate(reply.move, pos) > 0) exposed = true;
        }
        // Diagnostic hypothetical pass, not a claim that the opponent will pass.
        assert(!pos.in_check());
        pos.MakeNullMove();
        // Conservatively avoid claiming support from a pinned moving guard.
        if (guard && pos.pinned_pieces().test(move.to())) new_links = Bitboard();
        new_targets = CaptureTargets(pos) & ~before_targets;
        pos.UnmakeNullMove();
        pos.UnmakeMove(move);
        // Do not call a material-losing blocker or support move a safe receiver.
        // This does not suppress attack labels (pawn offers may initiate attacks).
        if (exposed) { blockade = false; new_links = Bitboard(); }
      }
      const bool defense = blockade || new_links.any();
      const char* role = forced ? "evasion" : tactical ? "tactical"
                       : defense && new_targets.any() ? "mixed"
                       : defense ? "defense" : new_targets.any() ? "attack" : "unknown";
      std::cout << index << ' ' << move.ToSfen() << ' ' << role << ' ' << blockade << ' ' << exposed;
      std::cout << " links";
      while (new_links.any()) std::cout << ':' << new_links.pop_first_one().ToSfen();
      std::cout << " threats";
      while (new_targets.any()) std::cout << ':' << new_targets.pop_first_one().ToSfen();
      std::cout << '\n';
      assert(pos.ToSfen() == original);
    }
  }
}
