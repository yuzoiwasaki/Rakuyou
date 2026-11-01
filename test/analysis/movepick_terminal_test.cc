// Terminal positions must reach search mate handling without probability scoring.
#ifdef NDEBUG
#error "Build this regression check with assertions enabled."
#endif
#include <cassert>
#include <iostream>
#include "bitboard.h"
#include "evaluation.h"
#include "extended_board.h"
#include "material.h"
#include "move_probability.h"
#include "movepick.h"
#include "position.h"
#include "progress.h"
#include "psq.h"
#include "stats.h"

int main(int argc, char** argv) {
  if (argc != 2) return 2;
  Square::Init(); Bitboard::Init(); ExtendedBoard::Init(); PsqPair::Init();
  Evaluation::ReadParametersFromFile(argv[1]); Material::Init();
  Position pos = Position::FromSfen(
      "ln2gk2l/5s+R2/p3p2p1/2ppsNp1p/1N1n5/2PBPPPb1/PP1P4P/1G2K1S2/+r4G2L w G2Pslp 1");
  HistoryStats history; history.Clear();
  GainsStats gains; gains.Clear();
  Array<Move, 2> empty = {kMoveNone, kMoveNone};
  Search::Stack stack[3] = {};
  for (int side = 0; side < 2; ++side) {
    assert(pos.IsOk() && pos.in_check());
    SimpleMoveList<kAllMoves, true> legal(pos);
    assert(legal.size() == 0);
    for (Depth depth : {MoveProbability::kAppliedDepth - kOnePly,
                        MoveProbability::kAppliedDepth,
                        MoveProbability::kAppliedDepth + kOnePly}) {
      MovePicker picker(pos, history, gains, depth, kMoveNone,
                        empty, empty, empty, stack + 2);
      if (depth < MoveProbability::kAppliedDepth) {
        // The shallow picker returns pseudo-legal evasions; search filters them.
        for (Move move = picker.NextMove(nullptr); move != kMoveNone;
             move = picker.NextMove(nullptr)) {
          assert(!pos.MoveIsLegal(move));
        }
      } else {
        assert(picker.NextMove(nullptr) == kMoveNone);
      }
      assert(picker.NextMove(nullptr) == kMoveNone);
    }
    pos.Flip();
  }
  std::cout << "Terminal move picker: both colors, three depths passed\n";
}
