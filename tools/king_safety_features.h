// Experimental shared residual features; existing evaluation remains the base.
#ifndef RAKUYOU_KING_SAFETY_FEATURES_H_
#define RAKUYOU_KING_SAFETY_FEATURES_H_

unsigned SafetyMask(Piece piece, int attacks, int defenses) {
  if (piece == kWall) return 0;
  unsigned mask = 0;
  if (piece == kBlackGold && defenses > 0) mask |= 1;
  if (piece == kBlackSilver && defenses > 0) mask |= 2;
  if ((piece == kBlackGold || piece == kBlackSilver) && defenses == 0) mask |= 4;
  if (attacks > defenses) mask |= 8;
  return mask;
}

std::array<int, 4> SafetyCounts(const Position& pos, Color color) {
  std::array<int, 4> counts{{0,0,0,0}};
  const Square king = pos.king_square(color);
  const ExtendedBoard& board = pos.extended_board();
  const EightNeighborhoods attacks = board.GetEightNeighborhoodControls(~color, king).LimitTo(3);
  const EightNeighborhoods defenses = board.GetEightNeighborhoodControls(color, king).Subtract(1).LimitTo(3);
  const EightNeighborhoods pieces = board.GetEightNeighborhoodPieces(king);
  for (int d = 0; d < 8; ++d) {
    Direction dir = static_cast<Direction>(d);
    Piece piece(pieces.at(dir));
    if (color == kWhite && piece != kWall && piece != kNoPiece) piece = piece.opponent_piece();
    const unsigned mask = SafetyMask(piece, attacks.at(dir), defenses.at(dir));
    for (int f = 0; f < 4; ++f) if (mask & (1u << f)) ++counts[f];
  }
  return counts;
}

void PrintSafety(std::ostream& out, const Position& pos) {
  out << "{\"black\":[";
  const auto black = SafetyCounts(pos, kBlack), white = SafetyCounts(pos, kWhite);
  for (int i=0;i<4;++i) { if(i) out << ','; out << black[i]; }
  out << "],\"white\":[";
  for (int i=0;i<4;++i) { if(i) out << ','; out << white[i]; }
  out << "]}";
}

void PrintSafetyMap() {
  std::cout << "{\"bytes\":" << sizeof(EvalParameters) << ",\"scale\":" << kFvScale
            << ",\"begin\":" << offsetof(EvalParameters, king_safety)
            << ",\"table_bytes\":" << sizeof(g_eval_params->king_safety) << ",\"entries\":[";
  bool first = true;
  for (unsigned h=HandSet::min(); h<=HandSet::max(); ++h)
    for (int d=0;d<8;++d)
      for (Piece piece : Piece::all_pieces().set(kNoPiece))
        for (int a=0;a<4;++a) for (int b=0;b<4;++b) {
          unsigned mask=SafetyMask(piece,a,b);
          if (!mask) continue;
          const PackedScore* value=&g_eval_params->king_safety[HandSet(h)][static_cast<Direction>(d)][piece][a][b];
          size_t offset=reinterpret_cast<const char*>(value)-reinterpret_cast<const char*>(g_eval_params.get());
          if (!first) std::cout << ',';
          first=false; std::cout << '[' << offset << ',' << mask << ']';
        }
  std::cout << "]}\n";
}
#endif
