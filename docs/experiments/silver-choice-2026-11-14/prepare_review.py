"""Render equal-depth candidate lines and verify every state; no search."""
import json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from tools.analysis.audit_white_positions import Board
CODE=Path(__file__).parent;OUT=ROOT/'results/teatsui-silver-choice-fixed-2026-11-14'
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
html='''<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>△４五歩に対する銀の選択</title><style>body{font-family:system-ui;max-width:1280px;margin:20px auto;padding:16px;background:#faf9f6;color:#222}p{line-height:1.7}.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}svg{width:100%;max-height:610px}button,select{font-size:16px;padding:8px;margin:3px}input{width:100%}pre{white-space:pre-wrap;overflow-wrap:anywhere}@media(max-width:700px){.grid{grid-template-columns:1fr}}</style><h1>△４五歩に、取る・引く・出る</h1><p><strong>左右とも下側の先手。左は以前の読み筋の▲同銀（３六から）、右は別の銀の動かし方です。</strong>▲７八金からの読み筋を46手目△４五歩まで進めた仮想局面で、実戦棋譜ではありません。８候補を同じ条件で深さ11まで読み切って比較しました。補正0・support10＋D10は変更していません。</p><select id="choose" onchange="choose(+this.value)"><option value="0">▲同銀（３六から）／▲５七銀（４六から）</option><option value="1">▲同銀（３六から）／▲５五銀（４六から）</option><option value="2">▲同銀（３六から）／▲同銀（４六から）</option><option value="3">▲同銀（３六から）／▲３五銀（４六から）</option><option value="4">▲同銀（３六から）／▲２七銀（３六から）</option><option value="5">▲同銀（３六から）／▲３五銀（３六から）</option><option value="6">▲同銀（３六から）／▲２五銀（３六から）</option></select><p id="note"></p><div><button onclick="show(0)">開始</button><button onclick="show(1)">比較の手</button><button onclick="show(4)">４手先</button><button onclick="show(8)">８手先</button><button onclick="show(n-1)">←１手</button><button onclick="show(n+1)">１手→</button></div><input id="seek" type="range" min="0" oninput="show(+this.value)" aria-label="開始からの手数"><p id="ply"></p><div class="grid" id="panels"></div><script>const cases=DATA;let c=0,n=1;SVG
function show(i){const x=cases[c],max=Math.max(...x.arms.map(a=>a.states.length-1));n=Math.max(0,Math.min(max,i));document.getElementById('seek').max=max;document.getElementById('seek').value=n;document.getElementById('ply').textContent=`総手数 ${x.rootply+n}`;document.getElementById('panels').innerHTML=x.arms.map((a,j)=>{const s=a.states[Math.min(n,a.states.length-1)];return `<section><h2>${j===0?'以前の読み筋の候補':'比較候補'}：${a.states[1].move}</h2><p>${s.ply}手目 ${s.move}${s.ply<x.rootply+n?'（保存読み筋終端）':''}</p>${svg(s)}<p>開始局面の候補評価：${a.score}cp（先手視点・深さ11）</p><details><summary>読み筋と局面</summary><p>${a.states.slice(1).map(t=>`${t.ply}: ${t.move}`).join(' → ')}</p><pre>${s.sfen}</pre></details></section>`}).join('');}
function choose(k){c=k;document.getElementById('choose').value=c;document.getElementById('note').textContent='▲５七銀（４六から）が今回の１位、▲５五銀（４六から）が２位でした。時間切れの８候補出力には未完了値が混ざったため、ここでは追加した固定深さ11の結果だけを表示しています。短い読みなので強制手順や優劣の証明ではありません。';show(1);}
document.addEventListener('keydown',e=>{if(['INPUT','SELECT'].includes(e.target.tagName))return;if(e.key==='ArrowLeft')show(n-1);if(e.key==='ArrowRight')show(n+1);});choose(0);</script></html>'''
(OUT/'review.html').write_text(html.replace('DATA',json.dumps(cases,ensure_ascii=False)).replace('SVG',svg))
(OUT/'review-check.json').write_text(json.dumps(dict(native_matched_states=len(allstates),new_searches=0),indent=2)+'\n');print('Verified displayed states:',len(allstates))
