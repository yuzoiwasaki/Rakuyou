"""Bounded fixed-depth paired games with a native rules referee and no retries."""
import argparse
from collections import Counter
import json
from pathlib import Path
import threading

from tools.analysis.paired_selfplay import UsiEngine
from tools.learning.data.prepare_learning_data import ROOT, Probe, digest
from tools.learning.hybrid.data import checked, load_dataset, output_path, write_json
from tools.learning.hybrid.runner import exclusive, seal, unseal
from tools.learning.playtest import behavior

SOURCE=behavior.SOURCE
OUTPUT=ROOT/'results/learning-pilot/2026-10-17-hybrid-match-v4'
STARTS=ROOT/'docs/experiments/configs/hybrid-match-starts-v1.json'
REFEREE=ROOT/'results/match-tools-v2/match-referee'
BUILD=ROOT/'results/match-tools-v2/build.json'
SETTINGS=dict(depth=15,timeout=300,max_additional_plies=256,threads=1,hash_mb=64,
              shin_yonenaga_gyoku=True,own_book=False,ponder=False,fresh_engines_per_game=True)


class RecordedEngine(UsiEngine):
    def __init__(self,path):
        self.commands=[]; self.transcript=[]; self.capture_lock=threading.Lock()
        super().__init__(Path(path),True,False,1,64,None,0)
    def send(self,command):
        self.commands.append(command)
        super().send(command)
    def _read_output(self):
        for line in self.process.stdout:
            line=line.rstrip('\n')
            with self.capture_lock:self.transcript.append(line)
            self.lines.put(line)
    def snapshot(self):
        with self.capture_lock:return dict(commands=list(self.commands),transcript=list(self.transcript))
    def close(self):
        if not hasattr(self,'process'):return
        try:super().close()
        finally:
            if self.process.poll() is None:self.process.kill(); self.process.wait(timeout=5)


def normalized(sfen):return ' '.join(sfen.split()[:3])


def dependencies():
    files=behavior.dependencies()
    for name in ('tools/learning/playtest/match.py','tools/analysis/paired_selfplay.py','tools/learning/playtest/build_referee.py'):
        files[name]=digest(ROOT/name)
    return files


def replay(probe,moves):
    state=probe.replay(moves)
    if not state.get('ok'):raise ValueError('Illegal history: '+str(state.get('error')))
    if state.get('result') not in ('ongoing','draw','black_win','white_win'):raise ValueError('Unknown referee result')
    return state


def games(starts):
    return [dict(number=2*i+j+1,pair=i+1,start_id=s['id'],moves=s['moves'],
                 candidate_color='black' if j==0 else 'white') for i,s in enumerate(starts) for j in range(2)]


def referee_bindings():
    build=json.loads(BUILD.read_text())
    if build['schema']!='match-referee-build-v1' or build['search_or_engine_build'] is not False:raise ValueError('Unexpected referee build')
    bindings={str(REFEREE):build['binary_sha256'],str(BUILD):digest(BUILD)}
    for entry in build['inputs']:
        bindings[str(ROOT/entry['source'])]=entry['source_sha256']
    for name,sha in build['headers'].items():bindings[str(ROOT/name)]=sha
    for path,sha in bindings.items():checked(path,sha)
    return bindings


def prepare(source=SOURCE,output=OUTPUT,starts=STARTS):
    source=Path(source).resolve(); output=output_path(output); starts=Path(starts).resolve()
    if output==source or output.is_relative_to(source):raise ValueError('Output must be outside source experiment')
    _,bindings,runtime,_=behavior.inputs(source)
    _,dataset=load_dataset(source)
    config=json.loads(starts.read_text())
    if config.get('schema')!='rakuyou-hybrid-match-starts-v1' or len(config['starts'])!=8:raise ValueError('Expected eight fixed match starts')
    bindings.update(referee_bindings())
    rows=config['starts']
    if len({r['id'] for r in rows})!=8 or any(not isinstance(r['id'],str) or not r['id'] for r in rows):raise ValueError('Invalid start IDs')
    if any(not isinstance(r['moves'],list) for r in rows):raise ValueError('Expected full move histories')
    old={normalized(r['sfen']) for r in dataset['rows']}; seen=set(); frozen=[]
    probe=Probe(REFEREE)
    try:
        for row in rows:
            state=replay(probe,row['moves']); root=state['positions'][-1]
            key=normalized(root['sfen'])
            if state['result']!='ongoing' or any(p['occurrences']>1 for p in state['positions']):raise ValueError('Terminal or repeated start history')
            if key in seen or key in old:raise ValueError('Duplicate start or historical learning root')
            seen.add(key); frozen.append(dict(id=row['id'],moves=row['moves'],sfen=root['sfen']))
    finally:probe.close()
    bindings.update({str(starts):digest(starts),str(REFEREE):digest(REFEREE),str(BUILD):digest(BUILD)})
    plan=dict(schema='rakuyou-hybrid-match-v1',source=str(source),settings=SETTINGS,starts=frozen,games=games(frozen),
              inputs_sha256=bindings,runtime_sha256=runtime,code_sha256=dependencies(),referee=str(REFEREE),
              engines=dict(baseline=str(source/'runtime/bin/release'),candidate=str(source/'search/runtime/bin/release')),
              limitation='Sixteen-game fixed-depth pilot, not an equal-time strength estimate; max-ply endings remain unresolved.')
    output.mkdir(parents=True,exist_ok=False); seal(output/'plan.json',plan)
    return plan


def load(output):
    output=output_path(output); plan=unseal(output/'plan.json')
    if plan['schema']!='rakuyou-hybrid-match-v1' or plan['settings']!=SETTINGS or plan['games']!=games(plan['starts']):raise ValueError('Match plan differs')
    if dependencies()!=plan['code_sha256']:raise ValueError('Match code changed')
    for group in ('inputs_sha256','runtime_sha256'):
        for path,sha in plan[group].items():checked(path,sha)
    _,bindings,runtime,_=behavior.inputs(Path(plan['source']))
    bindings.update(referee_bindings())
    if any(plan['inputs_sha256'].get(k)!=v for k,v in bindings.items()) or runtime!=plan['runtime_sha256']:raise ValueError('Source runtime bindings differ')
    expected={v:str(Path(plan['source'])/p) for v,p in [('baseline','runtime/bin/release'),('candidate','search/runtime/bin/release')]}
    if plan['engines']!=expected or plan['referee']!=str(REFEREE):raise ValueError('Executable path differs')
    return plan


def game_path(output,game):return output/'games'/f"{game['number']:02d}.json"


def snapshots(engines):return {name:engine.snapshot() for name,engine in engines.items()}


def play(game,plan,probe,engines,record,persist):
    moves=list(game['moves']); state=replay(probe,moves)
    for engine in engines.values():engine.new_game()
    record.update(moves=moves,records=[],status='incomplete',result='unresolved',reason=None)
    persist()
    for ply in range(plan['settings']['max_additional_plies']):
        if state['result']!='ongoing':
            record.update(status='completed',result=state['result'],reason=state['reason']);return
        color=state['positions'][-1]['side']
        if color not in ('black','white'):raise ValueError('Unknown side to move')
        player='candidate' if color==game['candidate_color'] else 'baseline'
        move,analysis,source=engines[player].choose_move(moves,plan['settings']['depth'],plan['settings']['timeout'])
        if any('error' in line.lower() or 'failed' in line.lower() for line in engines[player].snapshot()['transcript']):raise ValueError('Engine search error')
        record['records'].append(dict(ply=len(moves)+1,additional_ply=ply+1,color=color,player=player,move=move,analysis=analysis,source=source))
        persist()
        if move=='resign':
            record.update(status='completed',result='white_win' if color=='black' else 'black_win',reason='resign');return
        if move=='win':
            if state['positions'][-1]['can_declare'] is not True:raise ValueError('Invalid declaration')
            record.update(status='completed',result=color+'_win',reason='declaration');return
        if source!='search' or analysis is None:raise ValueError('Missing regular search analysis')
        flags=[]
        if analysis['score_type']=='mate':
            if not str(analysis['score']).lstrip('+-').isdigit() or int(analysis['score'])==0 or not 1<=analysis['depth']<=15:raise ValueError('Invalid mate search analysis')
            if analysis['depth']<15:flags.append('mate_early_depth')
        elif analysis['score_type']!='cp' or not 1<=analysis['depth']<=15:raise ValueError('Invalid search analysis depth/type')
        else:
            int(analysis['score'])
            # IterativeDeepening suppresses some final info lines. choose_move
            # returns only on bestmove; timeout raises and sends stop instead.
            # The last displayed depth/score/PV need not describe the final move.
            if analysis['depth']<15:flags.append('reported_depth_below_requested')
        if analysis.get('pv') and analysis['pv'][0]!=move:flags.append('reported_pv_differs_from_bestmove')
        if any(token in analysis['raw'].split() for token in ('lowerbound','upperbound')):flags.append('bounded_score')
        record['records'][-1]['diagnostics']=flags
        # Replay before accepting any move into the authoritative history.
        updated=replay(probe,moves+[move]); moves.append(move);state=updated
        record['moves']=list(moves);record['last_referee']=state;persist()
        if (ply+1)%20==0:print(f"  game {game['number']}: {ply+1} additional plies",flush=True)
    if state['result']!='ongoing':record.update(status='completed',result=state['result'],reason=state['reason'])
    else:record.update(status='completed',result='unresolved',reason='max_additional_plies')


def saved(output,plan):
    records={};binding=digest(output/'plan.json')
    for game in plan['games']:
        path=game_path(output,game); marker=path.with_suffix('.attempt.json')
        if not marker.exists():
            if path.exists() or path.with_suffix('.partial.json').exists():raise ValueError('Game missing attempt marker')
            continue
        if json.loads(marker.read_text())!=dict(number=game['number'],plan_sha256=binding):raise ValueError('Attempt binding differs')
        if not path.exists():raise ValueError('Incomplete game attempt blocks retry')
        record=unseal(path)
        if record['game']!=game or record['plan_sha256']!=binding or record['status'] not in ('completed','failed'):raise ValueError('Saved game binding differs')
        records[game['number']]=record
    return records


def aggregate(output,plan,records):
    totals=Counter();by_color={c:Counter() for c in ('black','white')}
    for record in records.values():
        color=record['game']['candidate_color']
        if record['status']=='failed':key='errors'
        elif record['result']=='unresolved':key='unresolved'
        elif record['result']=='draw':key='draws'
        else:key='wins' if record['result']==color+'_win' else 'losses'
        totals[key]+=1;by_color[color][key]+=1
    counts={k:totals[k] for k in ('wins','losses','draws','unresolved','errors')}
    complete_pairs=sum(all(n in records and records[n]['status']=='completed' for n in (2*i+1,2*i+2)) for i in range(len(plan['starts'])))
    report=dict(schema='rakuyou-hybrid-match-report-v1',plan_sha256=digest(output/'plan.json'),settings=plan['settings'],
                requested_games=len(plan['games']),attempted_games=len(records),completed_games=sum(r['status']=='completed' for r in records.values()),
                completed_pairs=complete_pairs,incomplete_pairs=len(plan['starts'])-complete_pairs,candidate=counts,
                by_color={c:{k:v[k] for k in counts} for c,v in by_color.items()},games=[records[n] for n in sorted(records)],limitation=plan['limitation'])
    seal(output/'report.json',report)
    text=f"Completed {report['completed_games']}/{report['requested_games']} games; complete pairs {complete_pairs}/{len(plan['starts'])}.\nCandidate: {counts}\n"+plan['limitation']+'\n'
    temporary=output/'summary.txt.tmp';temporary.write_text(text);temporary.replace(output/'summary.txt')
    return report


def run(output=OUTPUT):
    output=output_path(output);load(output)
    with exclusive(output/'run.lock'):
        plan=load(output);records=saved(output,plan);report=aggregate(output,plan,records)
        if any(r['status']=='failed' for r in records.values()):raise ValueError('Failed game blocks automatic continuation/retry')
        if len(records)==len(plan['games']):return report
        (output/'games').mkdir(exist_ok=True);probe=Probe(plan['referee'])
        try:
            for game in plan['games']:
                if game['number'] in records:continue
                print(f"Game {game['number']}/{len(plan['games'])}: {game['start_id']}, candidate {game['candidate_color']}",flush=True)
                path=game_path(output,game);binding=digest(output/'plan.json')
                write_json(path.with_suffix('.attempt.json'),dict(number=game['number'],plan_sha256=binding),exclusive=True)
                record=dict(game=game,plan_sha256=binding,status='incomplete',result='unresolved',reason=None,moves=list(game['moves']),records=[],engines={})
                engines={};failure=None
                def persist():
                    record['engines']=snapshots(engines);seal(path.with_suffix('.partial.json'),record)
                try:
                    persist()
                    for name,executable in plan['engines'].items():
                        engine=RecordedEngine.__new__(RecordedEngine);engines[name]=engine;engine.__init__(executable);persist()
                        if any('error' in line.lower() or 'failed' in line.lower() for line in engine.snapshot()['transcript']):raise ValueError('Engine loading error')
                    play(game,plan,probe,engines,record,persist)
                except BaseException as error:
                    failure=error;record.update(status='failed',result='error',failure=dict(type=type(error).__name__,message=str(error)))
                finally:
                    for engine in engines.values():
                        try:engine.close()
                        except Exception as error:
                            record.update(status='failed',result='error',failure=dict(type=type(error).__name__,message=str(error)));failure=error
                    persist();seal(path,record);records[game['number']]=record;report=aggregate(output,plan,records)
                if failure is not None:raise failure
        finally:
            probe.close();load(output)
        return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('prepare','run'));parser.add_argument('--output',type=Path,default=OUTPUT)
    parser.add_argument('--source',type=Path);parser.add_argument('--starts',type=Path)
    args=parser.parse_args()
    try:
        if args.command=='prepare':prepare(args.source or SOURCE,args.output,args.starts or STARTS);print(f'Prepared 8 starts / 16 games: {args.output}',flush=True)
        else:
            if args.source is not None or args.starts is not None:raise ValueError('--source/--starts are prepare-only')
            run(args.output);print((args.output/'summary.txt').read_text(),end='',flush=True)
    except (ValueError,OSError) as error:raise SystemExit(str(error)) from None


if __name__=='__main__':main()
