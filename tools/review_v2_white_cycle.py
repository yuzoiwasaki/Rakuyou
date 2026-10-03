#!/usr/bin/env python3
"""Read-only audit of three candidate positions across existing v2 White games.

Match board, hands and turn rather than opening text; count each game once
per position. Cohort outcomes are descriptive, not causal move comparisons.
The imported Board replays placement/ownership, not full legality or checks.
"""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from audit_white_positions import Board
from paired_selfplay import summarize


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUTS = [ROOT / "results" / name for name in (
    "shin-dedicated-v2-vs-normal-depth15-100games.json",
    "shin-dedicated-v2-repeat-vs-normal-depth15-100games.json",
    "shin-v2-white-only-depth15-100games.json",
)]
BASE = "7g7f 5a6b 2h6h 5c5d 3i3h 3a4b 5i4h 4b5c 4h3i 7a7b 6g6f 6b7a 7i7h 8c8d".split()
POSITIONS = {
    "common_silver67_gold58": BASE + "7h6g 2c2d 6i5h".split(),
    "after_silver67_pawn65": BASE + "7h6g 2c2d 6f6e".split(),
    "after_silver83_pawn96": BASE + "7h6g 2c2d 6i5h 3c3d 4g4f 7b8c 9g9f".split(),
}


def position_key(moves):
    board = Board()
    for move in moves:
        board.push(move)
    return board.sfen()


def stats(rows):
    counts = Counter(row["winner"] for row in rows)
    total = len(rows)
    return {
        "games": total,
        "wins": counts["shin_yonenaga"],
        "losses": counts["normal"],
        "draws": counts[None],
        "score_rate": ((counts["shin_yonenaga"] + counts[None] / 2) / total
                       if total else None),
    }


def review(paths):
    keys = {position_key(moves): name for name, moves in POSITIONS.items()}
    cohorts = {name: [] for name in POSITIONS}
    runs = []
    all_white = []
    for path in paths:
        raw = path.read_bytes()
        document = json.loads(raw)
        assert not document["errors"], path
        expected = document.get("requested_games", 100)
        assert isinstance(expected, int) and expected > 0, path
        assert len(document["games"]) == expected, path
        summary = summarize(document["games"], document["settings"].get("shin_side", "both"))
        summary["errors"] = 0
        assert summary == document["summary"], path
        white = []
        for number, game in enumerate(document["games"], 1):
            if game["white"] != "shin_yonenaga":
                continue
            assert game["black"] == "normal"
            assert game["moves"] == [r["move"] for r in game["records"]
                                     if r["move"] not in ("resign", "win")]
            assert game.get("game_number", number) == number
            row = {"run": path.name, "game_number": number, "winner": game["winner"]}
            white.append(row)
            all_white.append(row)
            board = Board()
            seen = set()
            for ply, record in enumerate(game["records"], 1):
                assert record["ply"] == ply
                assert record["color"] == ("black" if ply % 2 else "white")
                assert record["player"] == game[record["color"]]
                move = record["move"]
                if move in ("resign", "win"):
                    break
                name = keys.get(board.sfen())
                if name and name not in seen:
                    assert record["player"] == "shin_yonenaga"
                    cohorts[name].append(dict(row, ply=ply, move=move,
                                              moves_before=game["moves"][:ply - 1]))
                    seen.add(name)
                board.push(move)
        runs.append({"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(),
                     "settings": document["settings"], **stats(white)})
    positions = []
    for name, rows in cohorts.items():
        references = [{k: row[k] for k in ("run", "game_number", "ply", "move")}
                      for row in rows]
        positions.append({
            "id": name, "moves": POSITIONS[name], "sfen": position_key(POSITIONS[name]),
            **stats(rows),
            "by_run": [{"run": path.name, **stats([r for r in rows if r["run"] == path.name])}
                       for path in paths],
            "by_move": [{"move": move, **stats([r for r in rows if r["move"] == move])}
                        for move in sorted({r["move"] for r in rows})],
            "exact_canonical_prefix_games": sum(r["moves_before"] == POSITIONS[name] for r in rows),
            "references": references,
        })
    union = {(r["run"], r["game_number"]) for rows in cohorts.values() for r in rows}
    return {"runs": runs, "total_white": stats(all_white), "positions": positions,
            "unique_games_reaching_any_selected_position": len(union)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="*", type=Path)
    args = parser.parse_args()
    print(json.dumps(review(args.inputs or DEFAULT_INPUTS), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
