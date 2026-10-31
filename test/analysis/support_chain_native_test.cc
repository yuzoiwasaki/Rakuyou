// Standalone native check for the experimental evaluation term.
// Input: "sfen <SFEN>" or "moves <legal start-position moves>"; no search.
#ifdef NDEBUG
#error "This check must be built with assertions enabled."
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

void Check(Node& node, int bonus) {
  const EvalDetail full = Evaluation::EvaluateAll(node, PsqList(node));
  double progress = 0.0;
  const int score = full.ComputeFinalScore(node.side_to_move(), &progress);
  assert(node.Evaluate() == score);
  const int sign = int(Evaluation::HasPawnSupportChain(node,kBlack))
                 - int(Evaluation::HasPawnSupportChain(node,kWhite));
  assert(full.support_chain[0] == sign * bonus * kFvScale);
  for (int i=1;i<4;++i) assert(full.support_chain[i] == 0);
  EvalDetail base = full;
  base.support_chain = PackedScore(0);
  double base_progress = 0.0;
  const int base_score = base.ComputeFinalScore(node.side_to_move(), &base_progress);
  assert(progress == base_progress);
  assert(std::abs(score-base_score) <= bonus);
  // Truncation of signed totals can differ by less than two from the smooth delta.
  const double expected = bonus * (1.0-progress) * sign
      * (node.side_to_move()==kBlack ? 1 : -1);
  assert(std::abs((score-base_score)-expected) < 2.0);
}
int main(int argc,char** argv) {
  if(argc!=2) return 2;
  Square::Init();Bitboard::Init();ExtendedBoard::Init();Zobrist::Init();PsqPair::Init();
  Evaluation::ReadParametersFromFile(argv[1]);Material::Init();
  for(std::string line;std::getline(std::cin,line);) {
    const bool sfen=line.compare(0,5,"sfen ")==0;
    if(!sfen && line.compare(0,6,"moves ")!=0) return 2;
    for(int bonus : {0,10}) {
      Evaluation::SetSupportChainBonus(bonus);
      Node node(sfen ? Position::FromSfen(line.substr(5)) : Position::CreateStartPosition());
      std::vector<Move> moves;
      Check(node,bonus);
      if(!sfen) {
        std::istringstream input(line.substr(6));
        for(std::string token;input>>token;) {
          Move move=Move::FromSfen(token,node);
          assert(move.IsOk() && node.MoveIsLegal(move));
          node.MakeMove(move);moves.push_back(move);Check(node,bonus);
        }
      }
      if(!node.in_check()) {
        node.MakeNullMove();Check(node,bonus);node.UnmakeNullMove();Check(node,bonus);
      }
      std::cout << bonus << ' ' << int(Evaluation::HasPawnSupportChain(node,kBlack))
                << ' ' << int(Evaluation::HasPawnSupportChain(node,kWhite))
                << ' ' << node.Evaluate() << '\n';
      for(auto it=moves.rbegin();it!=moves.rend();++it) {
        node.UnmakeMove(*it);Check(node,bonus);
      }
    }
  }
}
