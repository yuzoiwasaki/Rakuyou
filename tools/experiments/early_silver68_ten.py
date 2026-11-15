#!/usr/bin/env python3
"""Ten targeted games: previous book vs conditional pawn46/bogin trial book."""
import argparse
import fcntl
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.experiments import early_silver68 as core
from tools.experiments.build_early_silver68_book import SOURCE, OUTPUT, build


def jobs():
    entries = {e['id']: e for e in json.loads(SOURCE.read_text())['entries']}
    contexts = [
        ('fourth-pawn46', entries['fourth_rook_prepare_silver47']['moves']),
        ('fourth-silver47', entries['fourth_rook_silver38_to47_after_king71']['moves']),
        ('bogin-silver83', entries['bogin-silver83-move17-ply17-4i5h']['moves']),
        ('bogin-silver74', entries['bogin-silver74-move19-ply19-4i5h']['moves']),
        ('static62-control', ['5i4h', '3c3d', '7i6h', '7a6b']),
    ]
    return [dict(id=f'{context}-{arm}', opening=context, arm=arm, prefix=list(prefix),
                 shin_book=str(book.relative_to(ROOT)), moves=[], records=[], positions={},
                 resumes=[], status='pending')
            for context, prefix in contexts
            for arm, book in [('previous', core.BOOK), ('candidate', OUTPUT)]]


def bindings():
    result = core.bindings()
    for p in [Path(__file__), SOURCE, OUTPUT,
              ROOT / 'tools/experiments/build_early_silver68_book.py']:
        result[str(p.relative_to(ROOT))] = core.sha(p)
    return result


def run(args, output):
    current = bindings()
    if OUTPUT.read_text() != build():
        raise SystemExit('Trial book differs from sources; rebuild before a new batch')
    if args.resume:
        if args.preflight:
            raise SystemExit('--resume uses saved settings')
        doc = json.loads(output.read_text())
        if doc.get('experiment') != 'early-silver68-conditional-ten-v1':
            raise SystemExit('Not a ten-game conditional trial result')
        if doc['bindings'] != current:
            raise SystemExit('Inputs changed; do not resume this batch')
    else:
        if output.exists():
            raise SystemExit('Output already exists; use --resume or a new filename')
        doc = dict(experiment='early-silver68-conditional-ten-v1',
                   created_at=core.timestamp(), bindings=current,
                   git_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                   settings=dict(depth=3 if args.preflight else 15,
                                 hash=64 if args.preflight else 512, threads=1,
                                 max_plies=256, shin_book_max_ply=32, normal_book_max_ply=20,
                                 preflight=args.preflight, preflight_added_plies=4 if args.preflight else None,
                                 black='ShinON/support10/D10', white='ShinOFF/support0/D0',
                                 both_books=True), games=jobs(), errors=[])
    core.save(doc, output)
    print(f'Results: {output}', flush=True)
    for number, g in enumerate(doc['games'], 1):
        if g['status'] not in ('pending', 'running', 'interrupted'):
            continue
        print(f"Game {number}/10: {g['id']}; fixed prefix={len(g['prefix'])}, saved={len(g['moves'])}", flush=True)
        settings = dict(doc['settings'])
        if settings['preflight']:
            settings['max_plies'] = len(g['prefix']) + settings['preflight_added_plies']
        try:
            if bindings() != doc['bindings']:
                raise ValueError('Inputs changed during batch')
            core.play(g, settings, lambda: core.save(doc, output))
        except KeyboardInterrupt:
            g['status'] = 'interrupted'
            core.save(doc, output)
            print('Interrupted; continue saved moves with --resume (fresh search hash).')
            return
        except Exception as error:
            g.update(status='error', reason=str(error))
            doc['errors'].append(dict(at=core.timestamp(), game=g['id'], message=str(error)))
            core.save(doc, output)
            raise
        hits = [r['ply'] for r in g['records'] if r['source'] == 'dedicated_book']
        print(f"  {g['status']}: {g['reason']}; winner={g.get('winner', '-')}; dedicated-book plies={hits}", flush=True)
    print('Finished 10-slot batch.', flush=True)
    print(json.dumps(doc['summary'], ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--output', type=Path)
    group.add_argument('--resume', type=Path)
    parser.add_argument('--preflight', action='store_true')
    args = parser.parse_args()
    output = (args.output or args.resume).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.with_suffix(output.suffix + '.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit('This result file is already in use')
        run(args, output)


if __name__ == '__main__':
    main()
