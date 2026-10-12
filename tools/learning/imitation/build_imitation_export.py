#!/usr/bin/env python3
"""Build isolated exporter from the frozen probe's exact sparse-table patch code."""
import sys,json,subprocess
from pathlib import Path
if not __package__:sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from tools.learning.data.prepare_learning_data import ROOT,digest
OUT=ROOT/'results/imitation-export-tools'


def build():
    OUT.mkdir(parents=True,exist_ok=False)
    source=ROOT/'tools/learning/native/imitation_probe.cc'
    text=source.read_text();anchor='int main(int argc,char** argv) {'
    if text.count(anchor)!=1:raise ValueError('Probe entry changed')
    text=text.split(anchor)[0]+r'''
#include <fcntl.h>
#include <unistd.h>
int main(int argc,char** argv) {
  if(argc!=4)return 2;
  Square::Init();Bitboard::Init();ExtendedBoard::Init();HuffmanCode::Init();PsqPair::Init();
  if(!LoadParams(argv[1]) || !Patch(argv[2]))return 2;
  const int fd=open(argv[3],O_WRONLY|O_CREAT|O_EXCL,0600);if(fd<0)return 2;
  const char* data=reinterpret_cast<const char*>(g_eval_params.get());size_t offset=0;
  while(offset<sizeof(EvalParameters)) {
    const ssize_t n=write(fd,data+offset,sizeof(EvalParameters)-offset);
    if(n<=0){close(fd);return 2;}offset+=size_t(n);
  }
  if(close(fd))return 2;
  std::cout<<"{\"bytes\":"<<sizeof(EvalParameters)<<",\"kp_offset\":"<<offsetof(EvalParameters,king_piece)
           <<",\"pp_offset\":"<<offsetof(EvalParameters,two_pieces)<<",\"controls_offset\":"<<offsetof(EvalParameters,controls)<<"}\n";
  return 0;
}
'''
    generated=OUT/'export.cc';generated.write_text(text)
    sources=sorted(str(p.relative_to(ROOT)) for p in (ROOT/'src').glob('*.cc') if p.name!='main.cc')+[str(generated.relative_to(ROOT))]
    command=['make','TARGET=gold-silver-pair-probe','executable','-j2','sources='+' '.join(sources),
        'object_dir=results/layout-build-check/obj','output_file=results/imitation-export-tools/export',
        'INCLUDES=-Isrc -Itools/learning/native -I'+subprocess.check_output(['xcrun','--show-sdk-path'],text=True).strip()+'/usr/include/c++/v1 -Ilib/libomp-x86_64/include']
    subprocess.run(command,cwd=ROOT,check=True)
    record=dict(command=command,probe_source_sha256=digest(source),generated_sha256=digest(generated),binary_sha256=digest(OUT/'export'),builder_sha256=digest(Path(__file__)))
    (OUT/'build.json').write_text(json.dumps(record,indent=2)+'\n')
if __name__=='__main__':build()
