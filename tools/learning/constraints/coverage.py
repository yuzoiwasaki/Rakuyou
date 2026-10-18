"""Saved-only descriptive coverage audit; events are not quality labels."""
import json
from collections import Counter
from pathlib import Path
from tools.analysis.audit_white_positions import Board
from tools.learning.data.prepare_learning_data import ROOT, digest

SOURCE=ROOT/'results/learning-pilot/2026-10-15-hybrid-v1'
SELECTION=ROOT/'results/learning-pilot/2026-10-13-outcome-expansion-selection-v1'
OUTPUT=ROOT/'results/learning-pilot/2026-10-18-training-coverage-v1'


def nearby(board, black):
    king=next(s for s,p in board.pieces.items() if p==('K' if black else 'k'))
    return {s for s,p in board.pieces.items() if p in (('G','S') if black else ('g','s'))
            and max(abs(int(s[0])-int(king[0])),abs(ord(s[1])-ord(king[1])))<=2}


def events(board,moves,black):
    counts=Counter();previous=None
    for move in moves:
        target=move[2:4];captured=board.pieces.get(target)
        piece=move[0] if move[1]=='*' else board.pieces[move[:2]]
        own=(board.ply%2==0)==black
        if captured:
            counts['captures']+=1
            if captured.upper() in ('G','S'):
                counts['gold_silver_captures']+=1
                if not own and target in nearby(board,black):counts['own_near_king_gs_captured']+=1
            if own and previous==target and piece.upper() in ('G','S'):
                counts['own_gs_immediate_recapture']+=1
        previous=target if captured else None
        board.push(move)
    return dict(counts)


def audit():
    dataset=json.loads((SOURCE/'dataset.json').read_text())
    teachers=json.loads((SOURCE/'teachers.json').read_text())
    assert digest(SOURCE/'dataset.json')==teachers['dataset_sha256']
    accepted={r['id']:r for r in teachers['records'] if r['status']=='accepted'}
    provenance={r['id']:r for split in ('train','validation')
                for r in json.loads((SELECTION/(split+'.roots.json')).read_text())['records']}
    inputs={str(p.relative_to(ROOT)):digest(p) for p in
            [SOURCE/'dataset.json',SOURCE/'teachers.json',SELECTION/'train.roots.json',SELECTION/'validation.roots.json']}
    cache={};rows=[]
    for row in dataset['rows']:
        if row['id'] not in accepted:continue
        src=provenance[row['id']]['source'];path=ROOT/src['path']
        if src['path'] not in cache:
            assert digest(path)==src['sha256']
            inputs[src['path']]=src['sha256'];cache[src['path']]=json.loads(path.read_text())
        game=cache[src['path']]['games'][row['game']-1];n=len(row['moves_before'])
        assert game['moves'][:n]==row['moves_before']
        assert game[row['side']]=='shin_yonenaga'
        black=row['side']=='black';b=Board()
        for move in row['moves_before']:b.push(move)
        assert b.sfen()==' '.join(row['sfen'].split()[:3])
        guards=len(nearby(b,black));actual=game['moves'][n:n+12]
        pv=accepted[row['id']]['analysis']['candidates'][0]['pv'][:12]
        actual_events=events(b,actual,black)
        b=Board()
        for move in row['moves_before']:b.push(move)
        pv_events=events(b,pv,black)
        rows.append(dict(id=row['id'],split=row['split'],side=row['side'],target=row['target'],
                         root_ply=n+1,progress=row['features']['progress'],near_king_gs=guards,
                         actual_plies=len(actual),pv_plies=len(pv),actual=actual_events,pv=pv_events))
    summaries={}
    for split in ('train','validation'):
        rs=[r for r in rows if r['split']==split]
        summaries[split]=dict(roots=len(rs),root_ply_bins=dict(Counter('24-40' if r['root_ply']<=40 else '41-60' if r['root_ply']<=60 else '61-80' for r in rs)),
            near_king_gs=dict(Counter(r['near_king_gs'] for r in rs)),
            progress_min=min(r['progress'] for r in rs),progress_max=max(r['progress'] for r in rs),
            progress_ge_half=sum(r['progress']>=.5 for r in rs),
            full_actual_window=sum(r['actual_plies']==12 for r in rs),full_pv_window=sum(r['pv_plies']==12 for r in rs),
            events={kind:{event:sum(r[kind].get(event,0)>0 for r in rs) for event in
                    ['captures','gold_silver_captures','own_near_king_gs_captured','own_gs_immediate_recapture']}
                    for kind in ['actual','pv']})
    return dict(inputs_sha256=inputs,code_sha256=digest(Path(__file__)),window_plies=12,rows=rows,summary=summaries,
                limitation='Descriptive event proxies, not thickness quality or causal labels. Actual lines differ from teacher PVs; PV nodes are not training rows. No search or learning.')


if __name__=='__main__':
    report=audit();OUTPUT.mkdir(parents=True,exist_ok=False)
    path=OUTPUT/'audit.json';path.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(report['summary'],indent=2));print('SHA256',digest(path))
