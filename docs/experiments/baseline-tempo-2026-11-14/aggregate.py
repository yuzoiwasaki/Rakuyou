"""Select complete same-depth lines and check frozen inputs; no searches."""
import json,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'results/teatsui-baseline-tempo-2026-11-14'
if '--fixed' in sys.argv: OUT=ROOT/'results/teatsui-baseline-tempo-fixed11-2026-11-14'
plan=json.loads((OUT/'plan.json').read_text());cases=[]
for item in plan['items']:
 r=json.loads((OUT/(item['id']+'.json')).read_text());assert r['status']=='complete' and r['bindings_unchanged']
 bydepth={}
 for row in r['infos']:
  if row.get('pv') and not row.get('bounds') and 'score' in row:
   key=row['pv'][0] if item['candidates'] else row['multipv']
   bydepth.setdefault(row['depth'],{})[key]=row
 keys=item['candidates'] or [1,2]
 depth=max(d for d,rows in bydepth.items() if all(k in rows for k in keys))
 cases.append(dict(id=item['id'],history=r['history'],common_depth=depth,bestmove=r['bestmove'],rows=[bydepth[depth][k] for k in keys],legal_pvs=r['pv_replayed'],wall_ms=r['wall_ms'],usi_ms=r['usi_ms']))
for p,d in plan['bindings'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==d
summary=dict(status='passed',searches=2,legal_pvs=sum(c['legal_pvs'] for c in cases),bindings_unchanged=True,score_perspective='white',cases=cases)
(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
for c in cases:
 print(c['id'],c['common_depth'])
 for r in c['rows']:print(r['score_type'],r['score'],r['pv'])
