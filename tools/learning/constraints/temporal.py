"""Select fixed later roots from existing games; no search or training."""
import json
from collections import Counter
from pathlib import Path
from tools.analysis.audit_white_positions import Board
from tools.learning.constraints.coverage import SOURCE, SELECTION
from tools.learning.constraints.alternate_match import keys
from tools.learning.data.prepare_learning_data import ROOT, Probe, digest

OUTPUT=ROOT/'results/learning-pilot/2026-10-18-temporal-selection-v1'
OFFSETS=(24,48)


def proposals(row,game):
    n=len(row['moves_before'])
    if game['moves'][:n]!=row['moves_before']:raise ValueError('Original history differs')
    return [(offset,n+offset) for offset in OFFSETS]


def prepare():
    dataset=json.loads((SOURCE/'dataset.json').read_text())
    teachers=json.loads((SOURCE/'teachers.json').read_text())
    if digest(SOURCE/'dataset.json')!=teachers['dataset_sha256']:raise ValueError('Dataset differs')
    accepted={r['id'] for r in teachers['records'] if r['status']=='accepted'}
    originals=[r for r in dataset['rows'] if r['id'] in accepted]
    provenance={r['id']:r['source'] for split in ('train','validation')
                for r in json.loads((SELECTION/(split+'.roots.json')).read_text())['records']}
    inputs={str(p.relative_to(ROOT)):digest(p) for p in
            [SOURCE/'dataset.json',SOURCE/'teachers.json',SELECTION/'train.roots.json',SELECTION/'validation.roots.json']}
    # Do not replace a rejected proposal with a nearby position. Reject collisions
    # symmetrically so neither split receives preference based on iteration order.
    oldkeys=set().union(*(keys(r['sfen']) for r in dataset['rows']))
    cache={};candidates=[];excluded=[];probe=Probe(ROOT/'results/match-tools-v2/match-referee')
    inputs['results/match-tools-v2/match-referee']=digest(ROOT/'results/match-tools-v2/match-referee')
    try:
        for row in originals:
            src=provenance[row['id']];path=ROOT/src['path']
            if src['path'] not in cache:
                if digest(path)!=src['sha256']:raise ValueError('Source game changed')
                inputs[src['path']]=src['sha256'];cache[src['path']]=json.loads(path.read_text())
            game=cache[src['path']]['games'][row['game']-1]
            if game[row['side']]!='shin_yonenaga':raise ValueError('Side differs')
            for offset,n in proposals(row,game):
                item=dict(id=f'{row["run"]}:{row["game"]}:{n+1}',parent_id=row['id'],split=row['split'],
                          run=row['run'],game=row['game'],side=row['side'],target=row['target'],offset=offset,ply=n+1)
                if n>=len(game['moves']):
                    excluded.append(dict(**item,reason='beyond_saved_moves'));continue
                moves=game['moves'][:n];state=probe.replay(moves)
                if not state.get('ok') or state.get('result')!='ongoing':
                    excluded.append(dict(**item,reason='illegal_or_terminal'));continue
                if any(p['occurrences']>1 for p in state['positions']):
                    excluded.append(dict(**item,reason='repeated_history'));continue
                root=state['positions'][-1];b=Board()
                for move in moves:b.push(move)
                if b.sfen()!=' '.join(root['sfen'].split()[:3]) or root['side']!=row['side']:
                    raise ValueError('Board/side mismatch')
                if keys(root['sfen']) & oldkeys:
                    excluded.append(dict(**item,reason='existing_root_collision'));continue
                candidates.append(dict(**item,moves_before=moves,sfen=root['sfen'],source=src['path']))
    finally:probe.close()
    counts=Counter(k for r in candidates for k in keys(r['sfen']))
    selected=[]
    for row in candidates:
        if any(counts[k]>1 for k in keys(row['sfen'])):
            excluded.append({**{k:v for k,v in row.items() if k not in ('moves_before','sfen','source')},'reason':'proposed_root_collision'})
        else:selected.append(row)
    summary={}
    for split in ('train','validation'):
        rs=[r for r in selected if r['split']==split];old=[r for r in originals if r['split']==split]
        per_game=Counter(r['parent_id'] for r in rs)
        summary[split]=dict(original=len(old),additional=len(rs),total=len(old)+len(rs),
            additions_per_game=dict(Counter(per_game[r['id']] for r in old)),
            after_ply80=sum(r['ply']>80 for r in rs),
            exclusions=dict(Counter(r['reason'] for r in excluded if r['split']==split)))
    report=dict(schema='temporal-root-selection-v1',offsets=list(OFFSETS),inputs_sha256=inputs,
        code_sha256={str(p.relative_to(ROOT)):digest(p) for p in [Path(__file__),ROOT/'tools/analysis/audit_white_positions.py',ROOT/'tools/learning/constraints/alternate_match.py']},
        original_ids=[r['id'] for r in originals],additional=selected,excluded=excluded,summary=summary,
        new_search_budget=len(selected),searches=0,updates=0,
        policy='Same games and run split; original plus24/48 plies; no score/progress/result filtering or refill. Equal game weights after teacher exclusions. Old validation remains exposed. Root collision audit only, not all historical positions.')
    OUTPUT.mkdir(parents=True,exist_ok=False);path=OUTPUT/'selection.json'
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(summary,indent=2));print('SHA256',digest(path))


if __name__=='__main__':prepare()
