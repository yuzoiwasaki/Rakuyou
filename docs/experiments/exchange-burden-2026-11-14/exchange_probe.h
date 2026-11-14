// Diagnostic only: immediate legal recaptures plus the existing approximate SEE.
// No score hook; intentionally excludes tempo, king safety, drops and other targets.
#include "swap.h"

template<Color side>
void PrintExchangeBurden(std::ostringstream& output, const Position& original) {
  Square target; int a=0,d=0;
  if(!RankOvercommitment<side>(original,&target,&a,&d)) {output << "null";return;}
  std::string sfen=original.ToSfen();const size_t turn=sfen.find(' ')+1;
  sfen[turn]=side==kBlack?'w':'b';
  Position pos=Position::FromSfen(sfen);
  // Avoid hypothetical turn-switch analysis when either king is already attacked.
  bool checking=false;
  for(Color c : {kBlack,kWhite})
    if(pos.king_exists(c) && pos.AttackersTo(pos.king_square(c),pos.pieces(),~c).any()) checking=true;
  if(checking) {output << "{\"skipped_check\":true}";return;}
  output << "{\"pawn\":\"" << target.ToSfen() << "\",\"captures\":[";
  bool first=true,burden=false;int legal_captures=0;
  Bitboard attackers=pos.AttackersTo(target,pos.pieces(),~side);
  while(attackers.any()) {
    const Square from=attackers.pop_first_one();
    for(bool promote : {false,true}) {
      const Piece piece=pos.piece_on(from);
      if(promote && (!piece.can_promote() || (!from.is_promotion_zone_of(~side) && !target.is_promotion_zone_of(~side)))) continue;
      Move capture(piece,from,target,promote,pos.piece_on(target));
      if(!pos.MoveIsLegal(capture)) continue;
      ++legal_captures;
      const int capture_see=int(Swap::Evaluate(capture,pos));
      pos.MakeMove(capture);int best=-100000,legal_recaptures=0;
      Bitboard defenders=pos.AttackersTo(target,pos.pieces(),side);
      if(!first) output << ',';first=false;
      output << "{\"move\":\"" << capture.ToSfen() << "\",\"capture_see\":" << capture_see << ",\"recaptures\":[";
      bool first_reply=true;
      while(defenders.any()) {
        const Square reply_from=defenders.pop_first_one();const Piece reply_piece=pos.piece_on(reply_from);
        for(bool reply_promote : {false,true}) {
          if(reply_promote && (!reply_piece.can_promote() || (!reply_from.is_promotion_zone_of(side) && !target.is_promotion_zone_of(side)))) continue;
          Move reply(reply_piece,reply_from,target,reply_promote,pos.piece_on(target));
          if(!pos.MoveIsLegal(reply)) continue;
          const int see=int(Swap::Evaluate(reply,pos));best=std::max(best,see);++legal_recaptures;
          if(!first_reply) output << ',';first_reply=false;
          output << "{\"move\":\"" << reply.ToSfen() << "\",\"see\":" << see << '}';
        }
      }
      output << "],\"best_recapture_see\":";
      if(legal_recaptures) output << best;else output << "null";
      const bool unsafe=!legal_recaptures || best<0;
      output << ",\"no_nonlosing_recapture\":" << (unsafe?"true":"false") << '}';
      burden=burden || unsafe;pos.UnmakeMove(capture);
    }
  }
  output << "],\"legal_captures\":" << legal_captures << ",\"local_burden\":" << (burden?"true":"false") << '}';
}
