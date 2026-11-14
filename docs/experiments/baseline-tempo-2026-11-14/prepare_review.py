"""Render equal-depth candidate lines and verify every state; no search."""
import json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from tools.analysis.audit_white_positions import Board
CODE=Path(__file__).parent;OUT=ROOT/'results/teatsui-baseline-tempo-fixed11-2026-11-14'
cases=json.loads((OUT/'summary.json').read_text())['cases']
labels={'P':'歩','L':'香','N':'桂','S':'銀','G':'金','B':'角','R':'飛','K':'玉','+P':'と','+L':'成香','+N':'成桂','+S':'成銀','+B':'馬','+R':'龍'}
titles=['46手目の構想：△６五銀／△４三銀','56手目：△５七香打／△５四銀（６五から）']
inputs=[];allstates=[]
for c,title in zip(cases,titles):
 c['title']=title;c['rootply']=len(c['history']);c['arms']=[]
 for row in c['rows']:
  b=Board()
  for m in c['history']:b.push(m)
  states=[]
  for i in range(len(row['pv'])+1):
   label='比較開始'
   if i:
    m=row['pv'][i-1];kind=m[0] if m[1]=='*' else b.pieces[m[:2]].upper();label=('▲' if b.ply%2==0 else '△')+m[2]+'一二三四五六七八九'[ord(m[3])-97]+labels[kind]+('打' if m[1]=='*' else '')+('成' if m.endswith('+') else '');b.push(m)
   state=dict(ply=c['rootply']+i,move=label,sfen=b.sfen(),pieces=[dict(file=int(s[0]),rank=ord(s[1])-96,label=labels[p.upper()],white=p[-1].islower()) for s,p in b.pieces.items()],hands=[' '.join(labels[k]+(str(n) if n>1 else '') for k,n in h.items() if n) or 'なし' for h in b.hands]);states.append(state);allstates.append(state);inputs.append('moves '+' '.join(c['history']+row['pv'][:i]))
  c['arms'].append(dict(score=row['score'],states=states))

from tools.learning.data.prepare_learning_data import Probe
from tools.learning.playtest.match import replay
probe=Probe(ROOT/'results/teatsui-baseline-review4-2026-11-14/referee/match-referee')
try:
 for c in cases:
  for row,arm in zip(c['rows'],c['arms']):
   assert row['score_type']=='cp' and row['depth']==11
   refs=replay(probe,c['history']+row['pv'])['positions'][len(c['history']):]
   for state,ref in zip(arm['states'],refs):assert state['sfen']==' '.join(ref['sfen'].split()[:3])
finally:probe.close()
source=(ROOT/'docs/experiments/rank-commitment-2026-11-13/continuation-review.html').read_text()
svg=source[source.index('function svg(s)'):source.index('function show(i)')].replace('先手（比較対象・新米長玉）','先手')
html=(CODE/'review-template.html').read_text().replace('/*DATA*/',json.dumps(cases,ensure_ascii=False)).replace('/*SVG*/',svg)
(OUT/'review.html').write_text(html)
(OUT/'review-check.json').write_text(json.dumps(dict(native_matched_states=len(allstates),searches=0),indent=2)+'\n')
print('Native matched states:',len(allstates))
