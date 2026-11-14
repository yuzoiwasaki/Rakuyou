"""Render four saved games; native replay references required, no search."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from tools.analysis.audit_white_positions import Board
from tools.learning.hybrid.runner import unseal
from tools.learning.data.prepare_learning_data import digest
OUT=ROOT/'results/teatsui-baseline-review4-2026-11-14'
audit=json.loads((OUT/'audit.json').read_text());assert audit['status']=='passed'
labels={'P':'歩','L':'香','N':'桂','S':'銀','G':'金','B':'角','R':'飛','K':'玉','+P':'と','+L':'成香','+N':'成桂','+S':'成銀','+B':'馬','+R':'龍'}
games={};count=0
for a in audit['games']:
 p=OUT/f"games/{a['number']:02}.json";assert digest(p)==a['sha256'];g=unseal(p);b=Board();states=[]
 refs=g['last_referee']['positions'];assert len(refs)==len(g['moves'])+1
 for i in range(len(g['moves'])+1):
  label='初期局面'
  if i:
   m=g['moves'][i-1];kind=m[0] if m[1]=='*' else b.pieces[m[:2]].upper();label=('▲' if b.ply%2==0 else '△')+m[2]+'一二三四五六七八九'[ord(m[3])-97]+labels[kind]+('打' if m[1]=='*' else '')+('成' if m.endswith('+') else '');b.push(m)
  assert b.sfen()==' '.join(refs[i]['sfen'].split()[:3])
  states.append(dict(ply=i,move=label,pieces=[dict(file=int(s[0]),rank=ord(s[1])-96,label=labels[p.upper()],white=p[-1].islower()) for s,p in b.pieces.items()],hands=[' '.join(labels[k]+(str(n) if n>1 else '') for k,n in h.items() if n) or 'なし' for h in b.hands],sfen=b.sfen()))
 games[a['number']]=dict(number=a['number'],color=a['color'],role=a['role'],result='勝ち' if g['result']==g['game']['candidate_color']+'_win' else '負け',states=states);count+=len(states)

source=(ROOT/'docs/experiments/rank-commitment-2026-11-13/continuation-review.html').read_text()
svg=source[source.index('function svg(s)'):source.index('function show(i)')].replace('先手（比較対象・新米長玉）','先手')
template=(Path(__file__).parent/'review-template.html').read_text()
(OUT/'review.html').write_text(template.replace('/*DATA*/',json.dumps(games,ensure_ascii=False)).replace('/*SVG*/',svg))
(OUT/'review-check.json').write_text(json.dumps(dict(native_matched_states=count,games=4,searches=0),indent=2)+'\n')
print('Native-matched displayed states:',count)
