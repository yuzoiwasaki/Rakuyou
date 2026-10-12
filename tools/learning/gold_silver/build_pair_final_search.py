#!/usr/bin/env python3
"""Build isolated evaluation copy for fixed selected-pair diagnostics; no bin writes."""

# Permit direct CLI execution as well as package imports.
import sys as _sys
from pathlib import Path as _RepoPath
if not __package__:
    _sys.path.insert(0, str(_RepoPath(__file__).resolve().parents[3]))
from pathlib import Path
import subprocess,json
from tools.learning.data.prepare_learning_data import ROOT, digest

OUT=ROOT/'results/pair-final-tools'

def build():
    OUT.mkdir(parents=True,exist_ok=True)
    probe_text=(ROOT/'tools/learning/native/gold_silver_pair_probe.cc').read_text()
    count=probe_text[probe_text.index('template<Color C>'):probe_text.index('\nvoid PrintPairs')]
    helper='''\n#include <cstdlib>
namespace {
'''+count+'''
int PairRaw(const char* name) {
  const char* value=std::getenv(name);
  if (!value) return 0;
  char* end=nullptr;long raw=std::strtol(value,&end,10);
  if (end==value || *end || raw < -32768 || raw > 32768) std::abort();
  return static_cast<int>(raw);
}
PackedScore PairSearchScore(const Position& pos) {
  static const int opening=PairRaw("RAKUYOU_PAIR_RAW_OPEN");
  static const int ending=PairRaw("RAKUYOU_PAIR_RAW_END");
  PackedScore score(0);
  if (!opening && !ending) return score;
  const int net=PairCount<kBlack>(pos)-PairCount<kWhite>(pos);
  score[0]=net*opening;score[2]=net*ending;
  return score;
}
} // namespace
'''
    original=ROOT/'src/evaluation.cc';source=original.read_text()
    anchor='Score EvalDetail::ComputeFinalScore('
    assert source.count(anchor)==1
    source=source.replace(anchor,helper+'\n'+anchor)
    replacements={'sum.king_safety = EvaluateKingSafety(pos);':'sum.king_safety = EvaluateKingSafety(pos) + PairSearchScore(pos);',
      'diff.king_safety = EvaluateKingSafety(pos) - previous_eval.king_safety;':'diff.king_safety = EvaluateKingSafety(pos) + PairSearchScore(pos) - previous_eval.king_safety;'}
    for before,after in replacements.items():
        assert source.count(before)==1;source=source.replace(before,after)
    generated=OUT/'evaluation.cc';generated.write_text(source)
    common=[p.relative_to(ROOT).as_posix() for p in sorted((ROOT/'src').glob('*.cc')) if p.name not in ('main.cc','evaluation.cc')]+[generated.relative_to(ROOT).as_posix()]
    sdk=subprocess.check_output(['xcrun','--show-sdk-path'],text=True).strip()
    includes=f'-Isrc -Itools -I{sdk}/usr/include/c++/v1 -Ilib/libomp-x86_64/include'
    flags='-Llib/libomp-x86_64/lib -Wl,-rpath,@loader_path/../../lib/libomp-x86_64/lib'
    for main,name in [('tools/learning/native/learning_data_probe.cc','probe'),('src/main.cc','engine')]:
        args=['make','TARGET=release','executable','-j2','sources='+' '.join(common+[main]),
              'object_dir=results/pair-final-tools/obj',f'output_file=results/pair-final-tools/{name}',
              'INCLUDES='+includes,'LDFLAGS='+flags]
        with (OUT/f'build-{name}.log').open('w') as log:
            subprocess.run(args,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
    record=dict(original_evaluation_sha256=digest(original),generated_evaluation_sha256=digest(generated),
      pair_definition_source_sha256=digest(ROOT/'tools/learning/native/gold_silver_pair_probe.cc'),
      source_sha256={p:digest(ROOT/p) for p in common+['src/main.cc','tools/learning/native/learning_data_probe.cc']},
      binaries={name:digest(OUT/name) for name in ('probe','engine')},tools_sha256=digest(Path(__file__)))
    (OUT/'build-manifest.json').write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
    print(json.dumps(record['binaries']))

if __name__=='__main__':build()
