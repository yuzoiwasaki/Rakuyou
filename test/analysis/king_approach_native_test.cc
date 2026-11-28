// Experimental king-approach feature: full/incremental, undo and symmetry.
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
#include "node.h"
#include "progress.h"
#include "psq.h"
#include "zobrist.h"

void Check(Node& node) {
  const auto full = Evaluation::EvaluateAll(node, PsqList(node));
  assert(full.ComputeFinalScore(node.side_to_move()) == node.Evaluate());
  Position flipped(node); flipped.Flip();
  for (Color side : {kBlack, kWhite}) {
    const int exposure = Evaluation::KingApproachExposure(node, side);
    assert(exposure >= 0 && exposure <= 8);
    assert(exposure == Evaluation::KingApproachExposure(flipped, ~side));
  }
}

int main(int argc, char** argv) {
  if (argc != 2) return 2;
  Square::Init(); Bitboard::Init(); ExtendedBoard::Init(); Zobrist::Init(); PsqPair::Init();
  Evaluation::ReadParametersFromFile(argv[1]); Material::Init();
  // A rook looks at the empty square two ranks ahead of the White king.
  // The supporting silver stops a direct check but not this approach feature.
  Position open = Position::FromSfen("9/3k5/3s5/9/9/9/9/9/3RK4 b - 1");
  Position blocked = Position::FromSfen("9/3k5/3s5/3p5/9/9/9/9/3RK4 b - 1");
  Position quiet = Position::FromSfen("9/3k5/3s5/9/9/9/9/9/4K4 b - 1");
  assert(Evaluation::KingApproachExposure(open, kWhite) > 0);
  assert(Evaluation::KingApproachExposure(blocked, kWhite) == 0);
  assert(Evaluation::KingApproachExposure(quiet, kWhite) == 0);
  open.Flip(); blocked.Flip(); quiet.Flip();
  assert(Evaluation::KingApproachExposure(open, kBlack) > 0);
  assert(Evaluation::KingApproachExposure(blocked, kBlack) == 0);
  assert(Evaluation::KingApproachExposure(quiet, kBlack) == 0);
  for (std::string line; std::getline(std::cin, line);) {
    const bool sfen = line.compare(0, 5, "sfen ") == 0;
    if (!sfen && line.compare(0, 6, "moves ") != 0) return 2;
    int base = 0;
    for (int penalty : {0, 10, 20, 40}) {
      Evaluation::SetKingApproachPenalty(penalty);
      Node node(sfen ? Position::FromSfen(line.substr(5)) : Position::CreateStartPosition());
      std::vector<Move> moves;
      Check(node);
      if (!sfen) {
        std::istringstream in(line.substr(6));
        for (std::string token; in >> token;) {
          const Move move = Move::FromSfen(token, node);
          assert(move.IsOk() && node.MoveIsLegal(move));
          node.MakeMove(move); moves.push_back(move); Check(node);
        }
      }
      if (!node.in_check()) {
        node.MakeNullMove(); Check(node); node.UnmakeNullMove(); Check(node);
      }
      const int black = Evaluation::KingApproachExposure(node, kBlack);
      const int white = Evaluation::KingApproachExposure(node, kWhite);
      double progress;
      const int score = Evaluation::EvaluateAll(node, PsqList(node)).ComputeFinalScore(node.side_to_move(), &progress);
      if (penalty == 0) base = score;
      const double expected = (white - black) * penalty * (1.0 - progress)
                            * (node.side_to_move() == kBlack ? 1 : -1);
      assert(std::abs(score - base - expected) < 2.0);
      std::cout << penalty << ' ' << black << ' ' << white << ' ' << score << '\n';
      for (auto it = moves.rbegin(); it != moves.rend(); ++it) {
        node.UnmakeMove(*it); Check(node);
      }
    }
  }
}
