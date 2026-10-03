#!/usr/bin/env python3
"""Read-only audit and branch review of the six existing paired Black datasets.

Replay checks placement/ownership/hands, not full legality or perpetual check.
Scores and cohorts are descriptive, not causal move-quality measurements.
"""

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from audit_white_positions import Board
from paired_selfplay import summarize


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUTS = [ROOT / "results" / f"{name}-vs-normal-depth15-100games.json"
                  for name in ("shin-book-off", "shin-book-on", "shin-dedicated-v1",
                               "shin-dedicated-v2", "shin-dedicated-v1-repeat",
                               "shin-dedicated-v2-repeat")]


def stats(rows):
    counts = Counter(r["game"]["winner"] for r in rows)
    n = len(rows)
    return dict(games=n, wins=counts["shin_yonenaga"], losses=counts["normal"],
                draws=counts[None], score_rate=(
                    (counts["shin_yonenaga"] + counts[None] / 2) / n if n else None))


def reference(row):
    return dict(run=row["run"], game_number=row["number"],
                pair=row["game"]["pair"], game_in_pair=row["game"]["game_in_pair"])


def groups(rows, key):
    buckets = defaultdict(list)
    for row in rows:
        buckets[key(row)].append(row)
    return [dict(key=k, **stats(v)) for k, v in
            sorted(buckets.items(), key=lambda item: (-len(item[1]), str(item[0])))]


def audit(document):
    games = document["games"]
    assert not document["errors"]
    assert len(games) == 2 * document["requested_pairs"] == 100
    assert document["settings"].get("shin_side", "both") == "both"
    summary = summarize(games)
    summary["errors"] = 0
    assert summary == document["summary"]
    for number, game in enumerate(games, 1):
        assert game["pair"] == (number + 1) // 2
        assert game["game_in_pair"] == (1 if number % 2 else 2)
        assert game["black"] == ("shin_yonenaga" if number % 2 else "normal")
        assert game["white"] == ("normal" if number % 2 else "shin_yonenaga")
        records = game["records"]
        assert game["moves"] == [r["move"] for r in records
                                 if r["move"] not in ("resign", "win")]
        counts = {player: Counter() for player in ("normal", "shin_yonenaga")}
        for ply, record in enumerate(records, 1):
            color = "black" if ply % 2 else "white"
            assert record["ply"] == ply and record["color"] == color
            assert record["player"] == game[color]
            counts[record["player"]][record["source"]] += 1
        assert {p: dict(c) for p, c in counts.items()} == game["source_counts_by_player"]
        assert dict(counts["normal"] + counts["shin_yonenaga"]) == game["source_counts"]
        if game["reason"] == "resign":
            assert records[-1]["move"] == "resign"
            assert game["winner"] == ("normal" if records[-1]["player"] == "shin_yonenaga"
                                      else "shin_yonenaga")
        elif game["reason"] == "max_plies":
            assert len(game["moves"]) == document["settings"]["max_plies"]
            assert game["winner"] is None
        else:
            raise AssertionError("Unexpected termination reason")
        assert game["result"] == ("draw" if game["winner"] is None else
                                  "black_win" if game["winner"] == game["black"]
                                  else "white_win")


def review(paths):
    runs, rows, drops = [], [], []
    positions = defaultdict(list)
    for path in paths:
        raw = path.read_bytes()
        document = json.loads(raw)
        audit(document)
        selected = []
        for number, game in enumerate(document["games"], 1):
            if game["black"] != "shin_yonenaga":
                continue
            assert game["moves"][0] == "5i4h"
            row = dict(run=path.name, number=number, game=game, king={}, cp={})
            normal = [r for r in game["records"] if r["player"] == "normal"]
            row["first_normal_search"] = next(
                r["ply"] for r in normal if r["source"] == "search")
            row["last_normal_book"] = max(
                (r["ply"] for r in normal if r["source"] == "book"), default=0)
            board, seen, previous = Board(), set(), None
            occurrences = Counter({board.sfen(): 1})
            row["four_occurrences"] = False
            for record in game["records"]:
                ply, move = record["ply"], record["move"]
                if move in ("resign", "win"):
                    continue
                sfen = board.sfen()
                if record["player"] == "shin_yonenaga" and 9 <= ply <= 25 and sfen not in seen:
                    positions[sfen].append(dict(row_ref=reference(row), move=move,
                                                 ply=ply, winner=game["winner"],
                                                 moves_before=game["moves"][:ply - 1]))
                    seen.add(sfen)
                analysis = record.get("analysis") or {}
                if record["player"] == "shin_yonenaga" and analysis.get("score_type") == "cp" and record["source"] == "search":
                    score = int(analysis["score"])
                    row["cp"][str(ply)] = score
                    if previous is not None and ply <= 61:
                        p, value = previous
                        drops.append(dict(**reference(row), before_ply=p, after_ply=ply,
                                          before=value, after=score, change=score-value,
                                          moves=game["moves"][p - 1:ply],
                                          winner=game["winner"]))
                    previous = (ply, score)
                board.push(move)
                occurrences[board.sfen()] += 1
                row["four_occurrences"] |= occurrences[board.sfen()] >= 4
                if ply in (24, 40, 60):
                    row["king"][str(ply)] = next(s for s, piece in board.pieces.items()
                                                  if piece == "K")
            selected.append(row)
        rows.extend(selected)
        runs.append(dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(),
                         settings=document["settings"], **stats(selected),
                         exits=groups(selected, lambda r: str(r["first_normal_search"]))))
    branches = []
    for prefix in [item["key"] for item in groups(rows, lambda r: " ".join(r["game"]["moves"][:6]))[:6]]:
        cohort = [r for r in rows if " ".join(r["game"]["moves"][:6]) == prefix]
        representatives = []
        for winner in ("shin_yonenaga", "normal", None):
            options = [r for r in cohort if r["game"]["winner"] == winner]
            if options:
                r = min(options, key=lambda r: len(r["game"]["moves"]))
                representatives.append(dict(**reference(r), winner=winner,
                    plies=len(r["game"]["moves"]), moves=r["game"]["moves"][:60],
                    king=r["king"], cp={p: v for p, v in r["cp"].items()
                                        if int(p) in (9, 19, 29, 39, 49, 59)}))
        branches.append(dict(prefix=prefix, **stats(cohort),
            by_run=[dict(run=path.name, **stats([r for r in cohort if r["run"] == path.name])) for path in paths],
            representatives=representatives))
    common = sorted(positions.items(), key=lambda item: (-len(item[1]), item[0]))[:12]
    return dict(runs=runs, total=stats(rows),
        prefix4=groups(rows, lambda r: " ".join(r["game"]["moves"][:4])),
        branches=branches, first_normal_search=groups(rows, lambda r: str(r["first_normal_search"])),
        last_normal_book=groups(rows, lambda r: str(r["last_normal_book"])),
        king={str(p): groups(rows, lambda r: r["king"].get(str(p), "ended")) for p in (24, 40, 60)},
        four_occurrences=stats([r for r in rows if r["four_occurrences"]]),
        frequent_positions=[dict(sfen=sfen, games=len(rs), moves=rs[0]["moves_before"],
            by_move=dict(Counter(r["move"] for r in rs)),
            outcomes=dict(Counter(str(r["winner"]) for r in rs))) for sfen, rs in common],
        diagnostic_drops=sorted(drops, key=lambda r: r["change"])[:12])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="*", type=Path)
    args = parser.parse_args()
    print(json.dumps(review(args.inputs or DEFAULT_INPUTS), ensure_ascii=False, indent=2))
