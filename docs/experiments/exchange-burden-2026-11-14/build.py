from pathlib import Path
import shutil,subprocess,json,hashlib,argparse
ROOT=Path(__file__).resolve().parents[3]
parser=argparse.ArgumentParser(description='Build a diagnostic probe in a new isolated output directory')
parser.add_argument('--output',type=Path,required=True)
OUT=parser.parse_args().output.resolve();OUT.mkdir(parents=True,exist_ok=False)
shutil.copy2(Path(__file__).with_name('exchange_probe.h'),OUT/'exchange_probe.h')
BASE=ROOT/'results/teatsui-rank-commitment-2026-11-13';SRC=OUT/'source'
shutil.copytree(BASE/'source',SRC,symlinks=True)
s=(BASE/'probe.cc').read_text().replace('#include "rank_commitment.h"','#include "rank_commitment.h"\n#include "exchange_probe.h"')
anchor='  output << ",\\\"king_safety\\\":[";';assert anchor in s
s=s.replace(anchor,'  output << ",\\\"exchange_black\\\":";PrintExchangeBurden<kBlack>(output,node);\n  output << ",\\\"exchange_white\\\":";PrintExchangeBurden<kWhite>(output,node);\n'+anchor)
(OUT/'probe.cc').write_text(s)
sdk=subprocess.check_output(['xcrun','--show-sdk-path'],text=True).strip();sources=[str(p.relative_to(SRC)) for p in sorted((SRC/'src').glob('*.cc')) if p.name!='main.cc']+['../probe.cc']
args=['make','TARGET=development','executable','-j2','sources='+' '.join(sources),'output_file=../native-probe','INCLUDES=-Isrc -I'+str(ROOT/'tools')+' -I'+sdk+'/usr/include/c++/v1 -Ilib/libomp-x86_64/include','LDFLAGS=-Llib/libomp-x86_64/lib -Wl,-rpath,'+str(ROOT/'lib/libomp-x86_64/lib')]
with (OUT/'build.log').open('x') as f:subprocess.run(args,cwd=SRC,stdout=f,stderr=subprocess.STDOUT,check=True)
print('Built exchange diagnostic, no evaluation hook.')
