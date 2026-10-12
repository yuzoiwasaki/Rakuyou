// Sparse KP/PP delta preparation; legacy parameter IO and score serialization.
#define main LegacyLearningProbeMain
#include "learning_data_probe.cc"
#undef main
#include <tuple>
#include <fstream>
#include <set>

namespace {
using Key3=std::tuple<int,int,int>; // type (0 KP / 1 PP), indices
std::map<Key3,int> Features(const Position&);
int Mirror(int index) {
  PsqIndex i(index);
  return i.square()==kSquareNone ? index : int(PsqIndex::OfBoard(i.piece(),Square::mirror_horizontal(i.square())));
}
int Rotate(int index) { return int(PsqPair::all_pairs()[PsqIndex(index)].white()); }
Key3 KpKey(int king,int index) {
  return std::min(Key3(0,king,index),Key3(0,int(Square::mirror_horizontal(Square(king))),Mirror(index)));
}
std::pair<Key3,int> PpKey(int a,int b) {
  auto pair=[](int x,int y) { return Key3(1,std::min(x,y),std::max(x,y)); };
  const Key3 direct=std::min(pair(a,b),pair(Mirror(a),Mirror(b)));
  const Key3 reverse=std::min(pair(Rotate(a),Rotate(b)),pair(Mirror(Rotate(a)),Mirror(Rotate(b))));
  if(direct==reverse) return std::make_pair(direct,0);
  return direct<reverse ? std::make_pair(direct,1) : std::make_pair(reverse,-1);
}
std::map<Key3,int> Features(const Position& pos) {
  std::map<Key3,int> counts;
  const PsqList list(pos);
  for(const PsqPair* i=list.begin();i!=list.end();++i) {
    ++counts[KpKey(int(pos.king_square(kBlack)),int(i->black()))];
    --counts[KpKey(int(Square::rotate180(pos.king_square(kWhite))),int(i->white()))];
    for(const PsqPair* j=list.begin();j<=i;++j) {
      const auto p=PpKey(int(i->black()),int(j->black()));counts[p.first]+=p.second;
    }
  }
  for(auto i=counts.begin();i!=counts.end();) { if(!i->second)i=counts.erase(i);else ++i; }
  return counts;
}
bool Patch(const char* path) {
  std::ifstream file(path);if(!file)return false;
  std::map<int32_t*,int32_t> edits;std::set<std::tuple<int,int,int,int>> seen;
  auto add=[&](int32_t* ptr,int32_t raw) {
    const auto found=edits.find(ptr);
    if(found!=edits.end() && found->second!=raw)return false;
    const int64_t n=int64_t(*ptr)+raw;
    if(n<std::numeric_limits<int32_t>::min() || n>std::numeric_limits<int32_t>::max())return false;
    edits[ptr]=raw;return true;
  };
  for(std::string line;std::getline(file,line);) {
    std::istringstream in(line);int type,a,b,lane;long long raw;std::string extra;
    if(!(in>>type>>a>>b>>lane>>raw) || (in>>extra) || raw<-kFvScale/2 || raw>kFvScale/2 || b<0 || b>PsqIndex::max())return false;
    if(!seen.insert(std::make_tuple(type,a,b,lane)).second)return false;
    if(type==0) {
      if(a<0 || a>Square::max() || lane<0 || lane>2 || KpKey(a,b)!=Key3(type,a,b))return false;
      if(!add(&g_eval_params->king_piece[Square(a)][PsqIndex(b)][lane],int32_t(raw)) ||
         !add(&g_eval_params->king_piece[Square::mirror_horizontal(Square(a))][PsqIndex(Mirror(b))][lane],int32_t(raw)))return false;
    } else if(type==1) {
      if(a<0 || a>PsqIndex::max() || (lane!=0 && lane!=2))return false;
      const auto p=PpKey(a,b);if(p.first!=Key3(type,a,b) || p.second!=1)return false;
      for(int rotation=0;rotation<2;++rotation) for(int mirror=0;mirror<2;++mirror) {
        int x=rotation?Rotate(a):a,y=rotation?Rotate(b):b;
        if(mirror){x=Mirror(x);y=Mirror(y);}
        const int32_t value=int32_t(rotation?-raw:raw);
        if(!add(&g_eval_params->two_pieces[PsqIndex(x)][PsqIndex(y)][lane],value) ||
           !add(&g_eval_params->two_pieces[PsqIndex(y)][PsqIndex(x)][lane],value))return false;
      }
    } else return false;
  }
  for(const auto& e:edits)*e.first+=e.second;
  return true;
}
void Print(const Position& pos) {
  Evaluation::SetShinYonenagaGyoku(true);
  const EvalDetail on=Evaluation::EvaluateAll(pos,PsqList(pos));
  Evaluation::SetShinYonenagaGyoku(false);
  const EvalDetail off=Evaluation::EvaluateAll(pos,PsqList(pos));
  double progress=0;const int value=on.ComputeFinalScore(pos.side_to_move(),&progress);
  std::ostringstream out;
  out << "{\"sfen\":\"" << Key(pos) << " 1\",\"eval_on\":" << value
      << ",\"eval_off\":" << off.ComputeFinalScore(pos.side_to_move())
      << ",\"progress\":" << std::setprecision(17) << progress << ",\"on_parts\":";
  PrintParts(out,on);out << ",\"off_parts\":";PrintParts(out,off);
  out << ",\"features\":[";bool first=true;
  for(const auto& e:Features(pos)) {
    if(!first)out<<',';first=false;
    out << '[' << std::get<0>(e.first) << ',' << std::get<1>(e.first) << ',' << std::get<2>(e.first) << ',' << e.second << ']';
  }
  out << "],\"kp_black\":[";
  for(int lane=0;lane<4;++lane){if(lane)out<<',';out<<on.kp[kBlack][lane];}
  out << "],\"kp_white\":[";
  for(int lane=0;lane<4;++lane){if(lane)out<<',';out<<on.kp[kWhite][lane];}
  out << "],\"pp\":[";
  for(int lane=0;lane<4;++lane){if(lane)out<<',';out<<on.two_pieces[lane];}
  out << "]}";std::cout<<out.str()<<'\n';
}
}
int main(int argc,char** argv) {
  if((argc!=3 && argc!=4) || std::string(argv[1])!="--features-sfen")return 2;
  Square::Init();Bitboard::Init();ExtendedBoard::Init();HuffmanCode::Init();PsqPair::Init();
  if(!LoadParams(argv[2]) || (argc==4 && !Patch(argv[3])))return 2;
  for(std::string line;std::getline(std::cin,line);){Print(Position::FromSfen(line));std::cout.flush();}
  return 0;
}
