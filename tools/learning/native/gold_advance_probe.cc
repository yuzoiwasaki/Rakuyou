// Static supported-gold advancement residual; reuse legacy legality, parameter IO and packed score output.
#define main LegacyLearningProbeMain
#include "learning_data_probe.cc"
#undef main

namespace {
std::array<int32_t,2> gold_raw{{0,0}};

template<Color C>
int GoldAdvanceScore(const Position& pos) {
  Bitboard supported;
  pos.pieces(C,kGold).ForEach([&](Square sq) {
    supported |= pos.AttacksFrom<C,kGold>(sq);
  });
  pos.pieces(C,kSilver).ForEach([&](Square sq) {
    supported |= pos.AttacksFrom<C,kSilver>(sq);
  });
  int score=0;
  pos.pieces(C,kGold).ForEach([&](Square sq) {
    if (!supported.test(sq)) return;
    const int advance=C==kBlack ? int(kRank8)-int(sq.rank()) : int(sq.rank())-int(kRank2);
    score+=std::min(3,std::max(0,advance));
  });
  return score;
}

void PrintGold(std::ostream& out,const Position& pos) {
  out << "{\"black\":" << GoldAdvanceScore<kBlack>(pos) << ",\"white\":" << GoldAdvanceScore<kWhite>(pos) << '}';
}

bool AddGold(EvalDetail* detail,int net) {
  for (int stage=0;stage<2;++stage) {
    const int lane=stage==0 ? 0 : 2;
    const int64_t changed=int64_t(detail->king_safety[lane])+int64_t(net)*gold_raw[stage];
    if (changed<std::numeric_limits<int32_t>::min() || changed>std::numeric_limits<int32_t>::max()) return false;
    detail->king_safety[lane]=static_cast<int32_t>(changed);
  }
  return true;
}

void GoldReplay(const std::string& line) {
  Position pos=Position::CreateStartPosition();
  std::istringstream input(line);std::string token;std::map<std::string,int> seen;std::ostringstream out;int ply=0;
  out << "{\"ok\":true,\"positions\":[";
  for (;;) {
    const std::string key=Key(pos);
    const HuffmanCode code=HuffmanCode::EncodePosition(pos);
    if (HuffmanCode::DecodePosition(code)!=pos) { std::cout << "{\"ok\":false,\"error\":\"huffman_roundtrip\"}\n";return; }
    char hex[65];const unsigned char* bytes=reinterpret_cast<const unsigned char*>(&code);
    for(int i=0;i<32;++i) std::snprintf(hex+2*i,3,"%02x",bytes[i]);
    if(ply) out << ',';
    const int net=GoldAdvanceScore<kBlack>(pos)-GoldAdvanceScore<kWhite>(pos);
    Evaluation::SetShinYonenagaGyoku(true);
    const EvalDetail baseline_on=Evaluation::EvaluateAll(pos,PsqList(pos));EvalDetail on=baseline_on;
    Evaluation::SetShinYonenagaGyoku(false);
    const EvalDetail baseline_off=Evaluation::EvaluateAll(pos,PsqList(pos));EvalDetail off=baseline_off;
    if(!AddGold(&on,net) || !AddGold(&off,net)) { std::cout << "{\"ok\":false,\"error\":\"gold_overflow\"}\n";return; }
    double progress=0;
    const int value=on.ComputeFinalScore(pos.side_to_move(),&progress);
    out << "{\"sfen\":\"" << key << " 1\",\"huffman_hex\":\"" << hex << "\",\"occurrences\":" << ++seen[key]
        << ",\"eval_on\":" << value << ",\"eval_off\":" << off.ComputeFinalScore(pos.side_to_move())
        << ",\"base_eval_on\":" << baseline_on.ComputeFinalScore(pos.side_to_move())
        << ",\"progress\":" << std::setprecision(17) << progress << ",\"gold_advance_scores\":";
    PrintGold(out,pos);
    out << ",\"on_parts\":";PrintParts(out,on);
    out << ",\"base_on_parts\":";PrintParts(out,baseline_on);
    out << ",\"off_parts\":";PrintParts(out,off);out << '}';
    if(!(input>>token)) break;
    Move move=kMoveNone;
    if(ply>=600 || !LegalToken(token,pos,&move)) { std::cout << "{\"ok\":false,\"error\":\"illegal_move\"}\n";return; }
    pos.MakeMove(move);++ply;
  }
  out << "]}";std::cout << out.str() << '\n';
}
}

int main(int argc,char** argv) {
  const bool sfen=argc==3 && std::string(argv[1])=="--gold-sfen";
  const bool perturb=argc==5 && std::string(argv[1])=="--gold-perturb";
  if(!sfen && !perturb && !(argc==3 && std::string(argv[1])=="--evaluate-details")) return 2;
  Square::Init();Bitboard::Init();ExtendedBoard::Init();HuffmanCode::Init();PsqPair::Init();
  if(!LoadParams(argv[2])) return 2;
  if(perturb) {
    for(int i=0;i<2;++i) {
      char* end=nullptr;errno=0;long long raw=std::strtoll(argv[3+i],&end,10);
      if(errno || end==argv[3+i] || *end || raw < -kFvScale/2 || raw>kFvScale/2) return 2;
      gold_raw[i]=static_cast<int32_t>(raw);
    }
  }
  for(std::string line;std::getline(std::cin,line);) {
    if(sfen) { const Position pos=Position::FromSfen(line);std::cout << "{\"gold_advance_scores\":";PrintGold(std::cout,pos);std::cout << "}\n"; }
    else GoldReplay(line);
    std::cout.flush();
  }
}
