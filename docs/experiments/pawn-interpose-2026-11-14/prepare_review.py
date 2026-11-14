"""Render equal-depth candidate lines and verify every state; no search."""
import json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from tools.analysis.audit_white_positions import Board
CODE=Path(__file__).parent;OUT=ROOT/'results/teatsui-pawn-interpose-2026-11-14'
cases=json.loads((CODE/'summary.json').read_text())['cases']
labels={'P':'歩','L':'香','N':'桂','S':'銀','G':'金','B':'角','R':'飛','K':'玉','+P':'と','+L':'成香','+N':'成桂','+S':'成銀','+B':'馬','+R':'龍'}
titles=[c['title'] for c in cases]
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
env={k:v for k,v in os.environ.items() if not k.startswith('RAKUYOU_')};env['RAKUYOU_RANK_COMMITMENT_CP']='10'
p=subprocess.run([str(ROOT/'results/teatsui-rank-commitment-2026-11-13/native-probe'),str(ROOT/'bin/params.bin'),'10','10'],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True,env=env,timeout=60)
refs=[json.loads(l) for l in p.stdout.splitlines()];assert len(refs)==len(allstates)
for state,r in zip(allstates,refs):assert r['ok'] and state['sfen']==' '.join(r['sfen'].split()[:3])
old=(ROOT/'docs/experiments/rank-commitment-2026-11-13/continuation-review.html').read_text();svg=old[old.index('function svg(s)'):old.index('function show(i)')]
html='''<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>▲５四歩打の比較</title><style>body{font-family:system-ui;max-width:1280px;margin:20px auto;padding:16px;background:#faf9f6;color:#222}p{line-height:1.7}.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}svg{width:100%;max-height:610px}button,select{font-size:16px;padding:8px;margin:3px}input{width:100%}pre{white-space:pre-wrap;overflow-wrap:anywhere}@media(max-width:700px){.grid{grid-template-columns:1fr}}</style><h1>▲５四歩打の狙いと取り方</h1><p>▲７八金〜▲５七銀の保存読み筋を48手目△５二飛まで進めた仮想局面です。各比較は固定深さ12・２候補表示で完了。補正0・support10＋D10のままです。予測手順であり、最善手や強制手順の証明ではありません。上側が後手、下側が先手です。</p><select id="choose" onchange="choose(+this.value)"><option value="0">49手目：▲５二龍／▲５四歩打</option><option value="1">△同銀の後：▲３三龍／▲３三角成</option><option value="2">▲５四歩打への応手：△同銀／△５六歩打</option></select><p id="note"></p><div><button onclick="show(0)">開始</button><button onclick="show(1)">比較の手</button><button onclick="show(4)">４手先</button><button onclick="show(8)">８手先</button><button onclick="show(n-1)">←１手</button><button onclick="show(n+1)">１手→</button></div><input id="seek" type="range" min="0" oninput="show(+this.value)" aria-label="開始からの手数"><p id="ply"></p><div class="grid" id="panels"></div><script>const cases=DATA;let c=0,n=1;SVG
function show(i){const x=cases[c],max=Math.max(...x.arms.map(a=>a.states.length-1));n=Math.max(0,Math.min(max,i));document.getElementById('seek').max=max;document.getElementById('seek').value=n;document.getElementById('ply').textContent=`総手数 ${x.rootply+n}`;document.getElementById('panels').innerHTML=x.arms.map((a,j)=>{const s=a.states[Math.min(n,a.states.length-1)];return `<section><h2>${j===0?'候補Ａ':'候補Ｂ'}：${a.states[1].move}</h2><p>${s.ply}手目 ${s.move}${s.ply<x.rootply+n?'（保存読み筋終端）':''}</p>${svg(s)}<p>開始局面の候補評価：${a.score}cp（${c===2?'後手':'先手'}視点・深さ12）</p><details><summary>読み筋と局面</summary><p>${a.states.slice(1).map(t=>`${t.ply}: ${t.move}`).join(' → ')}</p><pre>${s.sfen}</pre></details></section>`}).join('');}
function choose(k){c=k;document.getElementById('choose').value=c;document.getElementById('note').textContent=["先手（下側）の選択。▲５四歩打に後手は△５六歩打から銀を動かす読みです。","先手（下側）の取り方。直接▲３三龍だと△同角▲同角成で相手に飛車を渡します。先に▲３三角成△同角▲同龍なら、角交換をして龍を残せます。","後手（上側）の応手。すぐ△同銀なら５筋が銀で塞がります。先に△５六歩打として５七銀を動かす応手もあります。"][k];show(1);}
document.addEventListener('keydown',e=>{if(['INPUT','SELECT'].includes(e.target.tagName))return;if(e.key==='ArrowLeft')show(n-1);if(e.key==='ArrowRight')show(n+1);});choose(0);</script></html>'''
(OUT/'review.html').write_text(html.replace('DATA',json.dumps(cases,ensure_ascii=False)).replace('SVG',svg))
(OUT/'review-check.json').write_text(json.dumps(dict(native_matched_states=len(allstates),new_searches=0),indent=2)+'\n');print('Verified displayed states:',len(allstates))
