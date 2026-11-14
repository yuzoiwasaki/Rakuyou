import json,os,subprocess,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'results/teatsui-rank-trigger-review-2026-11-14';MATCH=ROOT/'results/teatsui-rank-counter-match-2026-11-14';TRIAL=ROOT/'results/teatsui-rank-commitment-2026-11-13'
audit=json.loads((MATCH/'audit.json').read_text());items=[]
for a in audit['games']:
 path=MATCH/f"games/{a['number']:02}.json";assert hashlib.sha256(path.read_bytes()).hexdigest()==a['sha256'];g=json.loads(path.read_text())
 for ply,state in enumerate(g['last_referee']['positions']):items.append(dict(game=a['number'],role=a['role'],candidate_color=a['color'],ply=ply,sfen=state['sfen'],move=g['moves'][ply-1] if ply else None))
rows={}
for cp in (0,10):
 env={k:v for k,v in os.environ.items() if not k.startswith('RAKUYOU_')};env['RAKUYOU_RANK_COMMITMENT_CP']=str(cp)
 r=subprocess.run([str(TRIAL/'native-probe'),str(ROOT/'bin/params.bin'),'10','10'],input=''.join('sfen '+x['sfen']+'\n' for x in items),text=True,capture_output=True,check=True,env=env,timeout=60)
 rows[cp]=[json.loads(s) for s in r.stdout.splitlines()];assert len(rows[cp])==len(items)
for item,off,on in zip(items,rows[0],rows[10]):
 assert off['ok'] and on['ok'];item.update(black=on['rank_black'],white=on['rank_white'],static_off=off['score'],static_on=on['score'],progress=on['progress'])
summary={}
for a in audit['games']:
 own=[x for x in items if x['game']==a['number']];active=[x for x in own if x['black'] or x['white']]
 summary[str(a['number'])]=dict(role=a['role'],candidate_color=a['color'],positions=len(own),active=len(active),active_plies=[x['ply'] for x in active],candidate_flagged=sum(x[a['color']] for x in own),opponent_flagged=sum(x['white' if a['color']=='black' else 'black'] for x in own))
for path,d in json.loads((TRIAL/'plan.json').read_text())['bindings'].items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==d
(OUT/'scan.json').write_text(json.dumps(dict(summary=summary,items=items),indent=2)+'\n');print(json.dumps(summary,indent=2))
