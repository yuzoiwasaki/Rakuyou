import json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'results/teatsui-rank-trigger-review-2026-11-14';BASE=ROOT/'results/teatsui-rank-commitment-2026-11-13'
scan=json.loads((OUT/'scan.json').read_text());pvs=json.loads((OUT/'pv-scan.json').read_text());positions={}
for x in scan['items']:
 if x['black'] or x['white']:positions.setdefault(x['sfen'],[]).append(dict(kind='actual',game=x['game'],ply=x['ply']))
for x in pvs['active']:positions.setdefault(x['sfen'],[]).extend(dict(kind='pv',**o) for o in x['occurrences'])
env={k:v for k,v in os.environ.items() if not k.startswith('RAKUYOU_')};env['RAKUYOU_RANK_COMMITMENT_CP']='10'
def run(binary):
 r=subprocess.run([str(binary),str(ROOT/'bin/params.bin'),'10','10'],input=''.join('sfen '+s+'\n' for s in positions),text=True,capture_output=True,check=True,env=env,timeout=60);rows=[json.loads(l) for l in r.stdout.splitlines()];assert len(rows)==len(positions);return rows
old=run(BASE/'native-probe');new=run(OUT/'native-probe');items=[]
for (sfen,origins),a,b in zip(positions.items(),old,new):
 assert {k:v for k,v in b.items() if not k.startswith('witness_')}==a
 item=dict(sfen=sfen,occurrences=origins,black=b['witness_black'],white=b['witness_white']);items.append(item)
(OUT/'witnesses.json').write_text(json.dumps(dict(positions=len(items),probe_parity=True,items=items),indent=2)+'\n')
for item in items:
 if any(o['game'] in (3,7) for o in item['occurrences']):print(json.dumps(item))
