"""Render all four saved pairs; native replay references required, no search."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from tools.analysis.audit_white_positions import Board
from tools.learning.hybrid.runner import unseal
from tools.learning.data.prepare_learning_data import digest
OUT=ROOT/'results/teatsui-rank-counter-match-2026-11-14'
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
 games[a['number']]=dict(number=a['number'],role=a['role'],result='勝ち' if g['result']==g['game']['candidate_color']+'_win' else '負け',states=states);count+=len(states)
pairs=[]
for p in audit['contrasts']['rank_effect']:
 pairs.append(dict(**p,color='先手（下側）' if p['pair']<3 else '後手（上側）',arms=[games[p['off_game']],games[p['on_game']]]))
old=(ROOT/'docs/experiments/rank-commitment-2026-11-13/continuation-review.html').read_text();svg=old[old.index('function svg(s)'):old.index('function show(i)')].replace('先手（比較対象・新米長玉）','先手')
html='''<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>補正0/10・８局の棋譜比較</title><style>body{font-family:system-ui;max-width:1280px;margin:20px auto;padding:16px;background:#faf9f6;color:#222}p{line-height:1.7}.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}svg{width:100%;max-height:600px}button,select{font-size:16px;padding:8px;margin:3px}input{width:100%}pre{white-space:pre-wrap;overflow-wrap:anywhere}@media(max-width:700px){.grid{grid-template-columns:1fr}}</style><h1>補正0／10：保存棋譜の比較</h1><p>左が補正0、右が補正10。どちらもsupport10＋D10。各組で新米長玉側を比較します。定跡固定12手を含む総手数です。実際の対局棋譜で、再探索はしていません。</p><select id="choose" onchange="choose(+this.value)"><option value="0">先手・対中飛車：両方負け</option><option value="1">先手・対居飛車：両方勝ち</option><option value="2">後手・対四間飛車：両方負け</option><option value="3" selected>後手・対三間飛車：補正0負け／10勝ち</option></select><p id="context"></p><div><button onclick="show(pairs[c].first_divergence.ply-1)">分岐直前</button><button onclick="show(30)">30手</button><button onclick="show(40)">40手</button><button onclick="show(48)">48手</button><button onclick="show(60)">60手</button><button onclick="show(n-1)">←１手</button><button onclick="show(n+1)">１手→</button></div><input id="seek" aria-label="総手数" type="range" min="0" oninput="show(+this.value)"><p id="ply"></p><div class="grid" id="panels"></div><script>const pairs=DATA;let c=3,n=40;SVG
function show(i){const pair=pairs[c],max=Math.max(...pair.arms.map(g=>g.states.length-1));n=Math.max(0,Math.min(max,i));document.getElementById('seek').max=max;document.getElementById('seek').value=n;document.getElementById('ply').textContent=`総手数 ${n}`;document.getElementById('panels').innerHTML=pair.arms.map((g,j)=>{const s=g.states[Math.min(n,g.states.length-1)];return `<section><h2>補正${j===0?0:10}・第${g.number}局</h2><p>新米長玉側の結果：${g.result} ／ ${s.ply}手目 ${s.move}${n>s.ply?'（棋譜終端で停止）':''}</p>${svg(s)}<details><summary>局面・直前の手順</summary><p>${g.states.slice(Math.max(1,s.ply-5),s.ply+1).map(t=>`${t.ply}: ${t.move}`).join(' → ')}</p><pre>${s.sfen}</pre></details></section>`}).join('');}
function choose(k){c=k;document.getElementById('choose').value=k;const p=pairs[c],d=p.first_divergence;document.getElementById('context').textContent=`今回見るのは両盤面の${p.color}（新米長玉）です。最初の分岐は${d.ply}手目、${d.player==='candidate'?'新米長玉側':'相手の通常版側'}。分岐後の違いには双方の応手と時間制限付き探索の揺れが含まれ、補正単独の効果とは断定できません。`;show(40);}
document.addEventListener('keydown',e=>{if(['INPUT','SELECT'].includes(e.target.tagName))return;if(e.key==='ArrowLeft')show(n-1);if(e.key==='ArrowRight')show(n+1);});choose(3);</script></html>'''
(OUT/'review.html').write_text(html.replace('DATA',json.dumps(pairs,ensure_ascii=False)).replace('SVG',svg))
(OUT/'review-check.json').write_text(json.dumps(dict(native_matched_states=count,games=8,searches=0),indent=2)+'\n');print('Native-matched displayed states:',count)

# Dedicated entry for the next review; all game data remain identical.
focused=html.replace('DATA',json.dumps(pairs,ensure_ascii=False)).replace('SVG',svg)
focused=focused.replace('choose(3);</script>', 'choose(0);show(44);</script>')
focused=focused.replace('<h1>補正0／10：保存棋譜の比較</h1>', '<h1>先手・対中飛車：中央の攻めと自陣の守り</h1><p><strong>今回は左右とも下側の先手（新米長玉）を見ます。</strong>左が補正0、右が補正10。両方とも最終的には負けました。初回分岐は23手目の端歩（左▲１六歩／右▲９六歩）です。</p><p>まず44手目で先手の駒の働きを比べ、48・58手目へ進めて攻防を見てください。左は成銀の侵入を許しながら５筋の飛車と歩を活用。右は47手目▲５五歩で動きますが、その後は玉側の攻防が続きます。勝敗だけでなく、どちらの構想に主張があるかを確認する比較です。表示は保存棋譜で、追加探索はしていません。</p>')
focused=focused.replace('<button onclick="show(40)">40手</button>', '<button onclick="show(44)">44手・攻防の前</button>')
focused=focused.replace('<button onclick="show(60)">60手</button>', '<button onclick="show(58)">58手・駒交換後</button><button onclick="show(72)">72手・その後</button>')
(OUT/'review-central.html').write_text(focused)

# Fourth-rook pair: White is the comparison side in both panels.
fourth=html.replace('DATA',json.dumps(pairs,ensure_ascii=False)).replace('SVG',svg)
fourth=fourth.replace('choose(3);</script>', 'choose(2);show(44);</script>')
fourth=fourth.replace('<h1>補正0／10：保存棋譜の比較</h1>', '<h1>後手・対四間飛車：受けと反撃の比較</h1><p><strong>今回は左右とも上側の後手（新米長玉）を見ます。</strong>左が補正0・第５局、右が補正10・第６局。両方とも最終的には負けました。初回分岐は相手側の19手目（左▲２八玉／右▲６六銀）です。</p><p>44手目から52・64手目へ進めて確認してください。左は角交換後、２筋と端へ攻めを向けます。右は△８四銀と出て、△５二飛で中央に対応しながら７・８筋で反撃します。終盤の勝敗だけでなく、駒の配置と攻めのタイミングを比較してください。追加探索はしていません。</p>')
fourth=fourth.replace('<button onclick="show(40)">40手</button>', '<button onclick="show(44)">44手・構え</button>')
fourth=fourth.replace('<button onclick="show(48)">48手</button>', '<button onclick="show(52)">52手・中央の対応</button>')
fourth=fourth.replace('<button onclick="show(60)">60手</button>', '<button onclick="show(64)">64手・反撃の進行</button><button onclick="show(74)">74手・その後</button>')
(OUT/'review-fourth.html').write_text(fourth)
