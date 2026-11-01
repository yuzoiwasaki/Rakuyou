// Regression checks for geometric recaptures in move-feature extraction.
#ifdef NDEBUG
#error "Build this regression check with assertions enabled."
#endif
#include <cassert>
#include <cctype>
#include <iostream>
#include <map>
#include <string>
#include "bitboard.h"
#include "evaluation.h"
#include "extended_board.h"
#include "material.h"
#include "move_feature.h"
#include "position.h"
#include "psq.h"
#include "stats.h"

using Pieces = std::map<std::string,std::string>;
std::string Sfen(const Pieces& pieces) {
  std::string out;
  for(char r='a';r<='i';++r) {
    int empty=0;
    for(char f='9';f>='1';--f) {
      auto it=pieces.find(std::string{f,r});
      if(it==pieces.end()) {++empty;continue;}
      if(empty) {out+=std::to_string(empty);empty=0;}
      out+=it->second;
    }
    if(empty) out+=std::to_string(empty);
    if(r!='i') out+='/';
  }
  return out+" b - 1";
}
std::string RotateSquare(const std::string& s) {
  return std::string{char('1'+'9'-s[0]),char('a'+'i'-s[1])};
}
void Case(Pieces pieces, std::string target, std::string from, bool promotion) {
  pieces["9a"]="k";pieces["1i"]="K";
  for(Color side : {kWhite,kBlack}) {
    Position pos=Position::FromSfen(Sfen(pieces));
    const Square to=Square::FromSfen(target);
    Bitboard attackers=side==kWhite ? pos.AttackersTo<kWhite>(to,pos.pieces())
                                   : pos.AttackersTo<kBlack>(to,pos.pieces());
    Move m=move_feature_detail::MakeRecapture(side,to,attackers,pos.extended_board());
    assert(m.IsOk() && m.from()==Square::FromSfen(from) && m.to()==to);
    assert(m.is_promotion()==promotion);
    ExtendedBoard after=pos.extended_board();after.MakeCaptureMove(m);
    assert(after.piece_on(to)==m.piece_after_move());
    assert(after.piece_on(m.from())==kNoPiece);
    assert(move_feature_detail::MakeRecapture(side,to,Bitboard(),pos.extended_board())==kMoveNone);
    Pieces rotated;
    for(const auto& p:pieces) {
      std::string pc=p.second;
      char& c=pc.back();c=std::islower(c) ? std::toupper(c) : std::tolower(c);
      rotated[RotateSquare(p.first)]=pc;
    }
    pieces=rotated;target=RotateSquare(target);from=RotateSquare(from);
  }
}
int main(int argc,char** argv) {
  if(argc!=2) return 2;
  Square::Init();Bitboard::Init();ExtendedBoard::Init();PsqPair::Init();
  Evaluation::ReadParametersFromFile(argv[1]);Material::Init();
  Case({{"1a","l"},{"9c","l"},{"9i","P"}},"9i","9c",true);
  Case({{"1a","l"},{"9c","l"},{"9h","S"}},"9h","9c",false);
  Case({{"4h","p"},{"4i","S"}},"4i","4h",true);
  Case({{"5g","n"},{"4i","P"}},"4i","5g",true);
  Case({{"5f","n"},{"4h","P"}},"4h","5f",true);
  Case({{"5e","n"},{"4g","P"}},"4g","5e",false);
  Case({{"4g","p"},{"4h","S"}},"4h","4g",false);
  Case({{"4h","+p"},{"4i","S"}},"4i","4h",false);
  Case({{"4h","p"},{"5h","s"},{"4i","S"}},"4i","4h",true);
  // Frozen position captured by a single diagnostic search of the failing root.
  Position pos=Position::FromSfen("kn5nl/2g2rs2/lp2p2pp/2gp1bp2/1Pp2p1P1/1B2L4/2NSPPP1P/4G1S2/5GKNL b SPr3p 1");
  Move sacrifice=Move::FromSfen("P*9i",pos);
  assert(pos.MoveIsLegal(sacrifice));
  HistoryStats history;history.Clear();GainsStats gains;gains.Clear();
  PositionInfo info(pos,history,gains,nullptr,nullptr);
  auto features=ExtractMoveFeatures(sacrifice,pos,info);
  assert(!features.empty());
  std::cout << "18 geometric cases and frozen full feature extraction passed\n";
}
