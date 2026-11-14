from pathlib import Path
import json,subprocess,os,importlib.util
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'results/teatsui-exchange-burden-2026-11-14';BASE=ROOT/'results/teatsui-rank-commitment-2026-11-13'
items=[dict(label=x['label'],input=x['input']) for x in json.loads((BASE/'static.json').read_text())['items']]
witnesses=json.loads((ROOT/'results/teatsui-rank-trigger-review-2026-11-14/witnesses.json').read_text())['items']
items += [dict(label='witness'+str(i),input='sfen '+x['sfen'],occurrences=x['occurrences']) for i,x in enumerate(witnesses)]
def sfen(p):
 ranks=[]
 for r in 'abcdefghi':
  row='';empty=0
  for f in range(9,0,-1):
   pc=p.get(str(f)+r)
   if pc:row+=(str(empty) if empty else '')+pc;empty=0
   else:empty+=1
  ranks.append(row+(str(empty) if empty else ''))
 return '/'.join(ranks)+' b - 1'
unsafe={'7a':'k','2i':'K','8e':'p','8d':'s','8h':'R','7g':'N'}
fixtures=[('knight_loss',unsafe,'white'),('knight_loss_mirror',{str(10-int(s[0]))+s[1]:p for s,p in unsafe.items()},'white'),('knight_loss_rotate',{str(10-int(s[0]))+chr(202-ord(s[1])):p.swapcase() for s,p in unsafe.items()},'black')]
items += [dict(label=n,input='sfen '+sfen(p),expected_side=side) for n,p,side in fixtures]
items.append(dict(label='pinned_knight',input='sfen '+sfen({'9a':'k','7i':'K','7a':'r','8e':'p','8d':'s','8h':'R','7g':'N'})))
items.append(dict(label='in_check_skip',input='sfen '+sfen({**unsafe,'2a':'r'})))
env={k:v for k,v in os.environ.items() if not k.startswith('RAKUYOU_')};env['RAKUYOU_RANK_COMMITMENT_CP']='10'
def run(binary):
 r=subprocess.run([str(binary),str(ROOT/'bin/params.bin'),'10','10'],input=''.join(x['input']+'\n' for x in items),capture_output=True,text=True,check=True,timeout=60,env=env)
 rows=[json.loads(x) for x in r.stdout.splitlines()];assert len(rows)==len(items) and all(x['ok'] for x in rows);return rows
old=run(BASE/'native-probe');new=run(OUT/'native-probe')
for item,a,b in zip(items,old,new):
 assert {k:v for k,v in b.items() if not k.startswith('exchange_')}==a,item['label']
 item['probe']=b
 if item.get('expected_side'):assert b['exchange_'+item['expected_side']]['local_burden'],item['label']
bylabel={x['label']:x for x in items}
assert bylabel['overmatched']['probe']['exchange_white']['local_burden'] is False
assert bylabel['rotate']['probe']['exchange_black']['local_burden'] is False
assert bylabel['no_guard']['probe']['exchange_white'] is None
assert bylabel['pinned_knight']['probe']['exchange_white']['local_burden'] is False
assert [c['move'] for c in bylabel['pinned_knight']['probe']['exchange_white']['captures']]==['8h8e']
assert bylabel['in_check_skip']['probe']['exchange_white']['skipped_check'] is True
summary=dict(positions=len(items),original_output_parity=True,synthetic_discrimination_passed=True,items=items)
(OUT/'checks.json').write_text(json.dumps(summary,indent=2)+'\n')
for item in items:
 if item['label'] in ('S8d_S7f','overmatched','knight_loss') or any(o.get('game')==7 and o.get('ply')==42 for o in item.get('occurrences',[])):print(item['label'],json.dumps({k:v for k,v in item['probe'].items() if k.startswith('exchange_')}))
print('checked',len(items))
