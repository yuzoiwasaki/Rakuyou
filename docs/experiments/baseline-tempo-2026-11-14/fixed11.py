"""Two fixed-depth checks after timed cutoff artifacts; no tuning or automatic retries."""
import hashlib,importlib.util,json,os,queue,subprocess,threading,time,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
OUT=ROOT/'results/teatsui-baseline-tempo-fixed11-2026-11-14'
BASE=ROOT/'results/teatsui-baseline-review4-2026-11-14'
RUNTIME=BASE/'runtime/support10d10'
s=importlib.util.spec_from_file_location('prior',ROOT/'results/teatsui-rook-foothold-2026-11-11/run.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
m.REFEREE=BASE/'referee/match-referee'
f=m.frozen_match(ROOT/'docs/experiments/baseline-review4-2026-11-14/match.py');f.load();f.checked_preflight()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(path,data):
 with path.open('x') as stream:json.dump(data,stream,indent=2);stream.write('\n')
game=json.loads((BASE/'games/03.json').read_text())
roots={'before46':game['moves'][:45],'before56':game['moves'][:55]}
items=[dict(id='before46',root='before46',candidates=[]),dict(id='before56',root='before56',candidates=['L*5g','6e5d'])]
assert game['moves'][55]=='L*5g'
bindings=json.loads((BASE/'plan.json').read_text())['bindings'].copy()
for p in [Path(__file__),Path(m.__file__),BASE/'games/03.json',BASE/'plan.json']:bindings[str(p)]=sha(p)
assert all(sha(p)==v for p,v in bindings.items())
probe=m.Probe(m.REFEREE)
try:
 for item in items:
  history=roots[item['root']];state=m.replay(probe,history);assert state['result']=='ongoing'
  for move in item['candidates']:m.replay(probe,history+[move])
finally:probe.close()
plan=dict(items=items,roots=roots,bindings=bindings,go="go depth 11",options=list(m.OPTIONS)+['setoption name KingContactDeficitBonus value 10'],limitation='Exactly two fresh fixed-depth11 MultiPV2 checks. Timed output contained interrupted-iteration mate sentinel in second line before46; complete-depth verification required. After45 unrestricted context; after55 restricted L*5g versus S6ex5d. Adopted support10/D10, ShinON, all RAKUYOU environment removed. Same-depth rows within each root; different positions cannot identify causal loss. No tuning, retries, adoption or long games.')
save(OUT/'plan.json',plan)
for item in items:
 assert all(sha(p)==v for p,v in bindings.items())
 history=roots[item['root']];name=item['id'];save(OUT/(name+'.attempt.json'),dict(item=item,plan_sha256=sha(OUT/'plan.json')))
 result=dict(status='incomplete',item=item,history=history,side='black' if len(history)%2==0 else 'white')
 env={k:v for k,v in os.environ.items() if not k.startswith('RAKUYOU_')};removed_environment=[k for k in os.environ if k.startswith('RAKUYOU_')]
 proc=None;lines=[];q=queue.Queue();commands=[]
 try:
  with (OUT/(name+'.raw.jsonl')).open('x',buffering=1) as raw:
   lock=threading.Lock()
   def journal(kind,text):
    with lock:raw.write(json.dumps(dict(kind=kind,text=text))+'\n')
   proc=subprocess.Popen([str(RUNTIME/'release')],cwd=RUNTIME,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
   def read():
    for line in proc.stdout:
     line=line.rstrip();journal('output',line);q.put(line)
    q.put(None)
   thread=threading.Thread(target=read,daemon=True);thread.start();deadline=time.monotonic()+30
   def send(c):
    commands.append(c);journal('command',c);proc.stdin.write(c+'\n');proc.stdin.flush()
   def wait(prefix):
    while True:
     line=q.get(timeout=max(.001,deadline-time.monotonic()))
     if line is None:raise RuntimeError('Early process exit')
     lines.append(line)
     if 'error' in line.lower() or 'failed' in line.lower():raise RuntimeError(line)
     if line.startswith(prefix):return line
   send('usi');wait('usiok')
   for option in plan['options']:send(option)
   send('setoption name MultiPV value 2');send('isready');wait('readyok');send('usinewgame')
   send('position startpos moves '+' '.join(history));start=time.monotonic();send(plan['go']+(' searchmoves '+' '.join(item['candidates']) if item['candidates'] else ''))
   result['bestmove']=wait('bestmove ').split()[1];result['wall_ms']=round(1000*(time.monotonic()-start))
   send('quit');proc.wait(timeout=5);thread.join(timeout=5);assert proc.returncode==0 and not thread.is_alive()
  infos=[r for line in lines if (r:=m.parse_info(line)) is not None]
  result['infos']=infos;result['last_unbounded']=m.last_unbounded(infos)
  result['pv_replayed']=m.audit_pvs(history,infos,result['bestmove'])
  timing=next(r for r in reversed(infos) if 'time' in r)
  result['usi_ms']=timing['time'];assert max(result['wall_ms'],result['usi_ms'])<3*max(1,min(result['wall_ms'],result['usi_ms']))
  assert all(sha(p)==v for p,v in bindings.items());result['bindings_unchanged']=True;result['status']='complete'
 except BaseException as error:
  result['failure']=repr(error);raise
 finally:
  if proc and proc.poll() is None:proc.kill();proc.wait()
  result['commands']=commands;save(OUT/(name+'.json'),result)
 print(json.dumps({k:result[k] for k in ('item','side','bestmove','wall_ms','pv_replayed','last_unbounded')},ensure_ascii=False),flush=True)
