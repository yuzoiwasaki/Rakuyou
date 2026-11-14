import json,os,subprocess
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from tools.analysis.audit_white_positions import Board
OUT=ROOT/'results/teatsui-rank-trigger-review-2026-11-14';MATCH=ROOT/'results/teatsui-rank-counter-match-2026-11-14';TRIAL=ROOT/'results/teatsui-rank-commitment-2026-11-13'
lines=[];positions={}
for num in (3,4,7,8):
 g=json.loads((MATCH/f'games/{num:02}.json').read_text())
 for r in g['records']:
  if r['player']!='candidate' or r['ply']>80 or not r.get('analysis',{}).get('pv'):continue
  pv=r['analysis']['pv'];history=g['moves'][:r['ply']-1];lines.append(dict(game=num,ply=r['ply'],history=history,pv=pv))
  b=Board()
  for m in history:b.push(m)
  for i in range(len(pv)+1):
   if i:b.push(pv[i-1])
   sfen=b.sfen()+' 1';positions.setdefault(sfen,dict(sfen=sfen,occurrences=[]))['occurrences'].append(dict(game=num,rootply=r['ply']-1,added=i))
env={k:v for k,v in os.environ.items() if not k.startswith('RAKUYOU_')};env['RAKUYOU_RANK_COMMITMENT_CP']='10'
def probe(inputs):
 r=subprocess.run([str(TRIAL/'native-probe'),str(ROOT/'bin/params.bin'),'10','10'],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True,timeout=60,env=env);rows=[json.loads(x) for x in r.stdout.splitlines()];assert len(rows)==len(inputs) and all(x['ok'] for x in rows);return rows
ends=probe(['moves '+' '.join(x['history']+x['pv']) for x in lines]);rows=probe(['sfen '+x for x in positions])
for item,r in zip(positions.values(),rows):item.update(black=r['rank_black'],white=r['rank_white'],progress=r['progress'])
active=[x for x in positions.values() if x['black'] or x['white']]
summary={str(num):dict(pvs=sum(x['game']==num for x in lines),active_prefix_occurrences=sum(o['game']==num for x in active for o in x['occurrences']),active_roots=sorted({o['rootply'] for x in active for o in x['occurrences'] if o['game']==num})) for num in (3,4,7,8)}
(OUT/'pv-scan.json').write_text(json.dumps(dict(scope='candidate saved PVs at moves13..80, games03/04/07/08; all prefixes, no search',unique_positions=len(positions),legal_pvs=len(lines),summary=summary,active=active),indent=2)+'\n');print(json.dumps(dict(unique_positions=len(positions),legal_pvs=len(lines),active_unique=len(active),summary=summary),indent=2))
