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
    const int pressure = Evaluation::GuardExchangeExposure(node, side);
    assert(pressure >= 0 && pressure <= 8);
    assert(pressure == Evaluation::GuardExchangeExposure(flipped, ~side));
    const int deficit = Evaluation::GuardCoverageDeficit(node, side);
    assert(deficit >= 0 && deficit <= 12);
    assert(deficit == Evaluation::GuardCoverageDeficit(flipped, ~side));
  }
}

int main(int argc, char** argv) {
  if (argc != 2 && argc != 3) return 2;
  const std::string mode = argc == 3 ? argv[2] : "approach";
  if (mode != "approach" && mode != "exchange" && mode != "coverage") return 2;
  const bool exchange = mode == "exchange";
  const bool coverage = mode == "coverage";
  const auto exposure = coverage ? Evaluation::GuardCoverageDeficit
                      : exchange ? Evaluation::GuardExchangeExposure
                                 : Evaluation::KingApproachExposure;
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
  // A supported pawn drop on64 attacks S63, whose capture abandons G72.
  Position threat = Position::FromSfen("9/2gk5/3s5/9/9/9/9/9/3RK4 b P 1");
  Position sealed = Position::FromSfen("9/2gk5/3s5/3p5/9/9/9/9/3RK4 b P 1");
  Position no_pawn = Position::FromSfen("9/2gk5/3s5/9/9/9/9/9/3RK4 b - 1");
  Position nifu = Position::FromSfen("9/2gk5/3s5/9/3P5/9/9/9/3RK4 b P 1");
  Position no_support = Position::FromSfen("9/2gk5/3s5/9/9/9/9/9/4K4 b P 1");
  Position actual_pawn = Position::FromSfen("9/2gk5/3s5/3P5/9/9/9/9/3RK4 b - 1");
  for (int flip = 0; flip < 2; ++flip) {
    const Color side = flip == 0 ? kWhite : kBlack;
    assert(Evaluation::GuardExchangeExposure(threat, side) > 0);
    assert(Evaluation::GuardExchangeExposure(actual_pawn, side) > 0);
    assert(Evaluation::GuardExchangeExposure(sealed, side) == 0);
    assert(Evaluation::GuardExchangeExposure(no_pawn, side) == 0);
    assert(Evaluation::GuardExchangeExposure(nifu, side) == 0);
    assert(Evaluation::GuardExchangeExposure(no_support, side) == 0);
    threat.Flip(); sealed.Flip(); no_pawn.Flip(); nifu.Flip(); no_support.Flip(); actual_pawn.Flip();
  }
  Position bare = Position::FromSfen("9/3k5/9/9/9/9/9/9/4K4 b - 1");
  Position single = Position::FromSfen("9/3k5/3g5/9/9/9/9/9/4K4 b - 1");
  Position redundant = Position::FromSfen("9/3k5/3gs4/9/9/9/9/9/4K4 b - 1");
  for (int flip = 0; flip < 2; ++flip) {
    const Color side = flip == 0 ? kWhite : kBlack;
    assert(Evaluation::GuardCoverageDeficit(bare, side) == 12);
    assert(Evaluation::GuardCoverageDeficit(single, side) == 7);
    assert(Evaluation::GuardCoverageDeficit(redundant, side) == 5);
    bare.Flip(); single.Flip(); redundant.Flip();
  }
  for (std::string line; std::getline(std::cin, line);) {
    const bool sfen = line.compare(0, 5, "sfen ") == 0;
    if (!sfen && line.compare(0, 6, "moves ") != 0) return 2;
    int base = 0;
    for (int penalty : {0, 10, 20, 40}) {
      Evaluation::SetKingApproachPenalty((exchange || coverage) ? 0 : penalty);
      Evaluation::SetGuardExchangePenalty(exchange ? penalty : 0);
      Evaluation::SetGuardCoveragePenalty(coverage ? penalty : 0);
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
      const int black = exposure(node, kBlack);
      const int white = exposure(node, kWhite);
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
