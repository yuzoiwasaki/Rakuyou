#!/usr/bin/env python3
"""Prepare independent selected-candidate runtimes; USI readiness only, no go."""
import argparse
import json
import shutil
from pathlib import Path

from prepare_learning_data import ROOT,digest
from check_selected_qsearch import locked_candidate
from validate_learning_input import load_input
from analyze_positions import Engine

SETTINGS=dict(depth=12,multipv=1,threads=1,hash_mb=64,timeout=30,
              shin_yonenaga_gyoku=True,own_book=False,ponder=False,
              fresh_engine_per_position=True,max_searches=24)


def copy_verified(source,target,expected):
    if digest(source)!=expected:raise ValueError("Source SHA mismatch")
    target.parent.mkdir(parents=True,exist_ok=True)
    with source.open('rb') as src,target.open('xb') as dst:shutil.copyfileobj(src,dst)
    shutil.copymode(source,target)
    if (digest(source)!=expected or digest(target)!=expected or
            source.stat().st_ino==target.stat().st_ino):
        raise ValueError("Copy integrity/independence failure")


def select_positions(parts,review):
    result=[]
    for split in ('validation','test'):
        rows={r['id']:r for r in parts[split]}
        seen=set()
        for record in review['records'][split]:
            if record['stratum'] in seen:continue
            row=rows[record['id']]
            if row['run']!=record['run'] or row['sfen']!=record['base']['root_sfen']:
                raise ValueError("Review/input mismatch")
            seen.add(record['stratum'])
            result.append(dict(id=row['id'],split=split,stratum=row['stratum'],
                               sfen=row['sfen'],moves=row['moves_before']))
        if len(seen)!=6:raise ValueError("Need all six previously diagnosed strata")
    return result


class ReadyEngine(Engine):
    def __init__(self,path):
        self.transcript=[]
        try:super().__init__(path,1,64,1,True)
        except BaseException:
            if hasattr(self,'process'):self.close()
            raise

    def _read_output(self):
        for line in self.process.stdout:
            self.transcript.append(line.rstrip('\n'))
            self.lines.put(line.rstrip('\n'))


def readiness(path):
    engine=ReadyEngine(path)
    try:
        if any('failed' in line.lower() or 'error' in line.lower() for line in engine.transcript):
            raise ValueError('Engine reported a loading error')
    finally:engine.close()
    return engine.transcript


def prepare(manifest_path,pilot_path,review_path,output):
    output=Path(output).resolve()
    if not output.is_relative_to((ROOT/'results').resolve()):
        raise ValueError('Output must be inside ignored results')
    pilot,candidate=locked_candidate(pilot_path)
    manifest,parts=load_input(manifest_path)
    if digest(manifest_path)!=pilot['binding']['manifest_sha256']:
        raise ValueError('Pilot input mismatch')
    review=json.loads(Path(review_path).read_bytes())
    if (review.get('schema')!='rakuyou-selected-qsearch-check-v1' or
            review['pilot_report_sha256']!=digest(pilot_path) or
            review['candidate_sha256']!=digest(candidate) or
            review['manifest_sha256']!=digest(manifest_path)):
        raise ValueError('Selected-candidate review mismatch')
    runtime={n:digest(ROOT/n) for n in manifest['runtime_sha256']}
    if runtime!=pilot['runtime_sha256']:raise ValueError('Runtime mismatch')
    positions=select_positions(parts,review)
    output.mkdir(parents=True,exist_ok=False)
    entries=[];ready={}
    for variant in ('baseline','candidate'):
        files={n:ROOT/n for n in runtime}
        files['lib/libomp-x86_64/lib/libomp.dylib']=ROOT/'lib/libomp-x86_64/lib/libomp.dylib'
        if variant=='candidate':files['bin/params.bin']=candidate
        for name,source in files.items():
            target=output/variant/name
            sha=digest(source)
            copy_verified(source,target,sha)
            entries.append(dict(variant=variant,path=str(target.relative_to(output)),
                                source=str(source.relative_to(ROOT)),sha256=sha,bytes=target.stat().st_size))
        ready[variant]=readiness(output/variant/'bin/release')
    if runtime!={n:digest(ROOT/n) for n in runtime}:raise ValueError('Runtime changed')
    for e in entries:
        if digest(output/e['path'])!=e['sha256']:raise ValueError('Sidecar changed during readiness')
    with (output/'positions.json').open('x') as stream:
        json.dump(dict(positions=positions),stream,ensure_ascii=False,indent=2);stream.write('\n')
    report=dict(schema='rakuyou-tempo-search-preparation-v1',files=entries,
                settings=SETTINGS,positions_sha256=digest(output/'positions.json'),
                pilot_report_sha256=digest(pilot_path),review_sha256=digest(review_path),
                manifest_sha256=digest(manifest_path),runtime_sha256=runtime,
                readiness_transcripts=ready,searches_executed=0,real_data_updates=0,
                deployed=False,test_quality_newly_measured=0,
                tool_sha256=digest(Path(__file__)))
    with (output/'manifest.json').open('x') as stream:
        json.dump(report,stream,ensure_ascii=False,sort_keys=True,indent=2);stream.write('\n')
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('manifest',type=Path);p.add_argument('pilot_report',type=Path)
    p.add_argument('review',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=prepare(a.manifest,a.pilot_report,a.review,a.output)
    print(json.dumps(dict(files=len(r['files']),ready=list(r['readiness_transcripts']),
                          settings=r['settings'],searches_executed=0),indent=2))


if __name__=='__main__':main()
