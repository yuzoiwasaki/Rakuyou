#!/usr/bin/env python3
"""Compile reviewed White candidates into Rakuyou's small position book."""

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = ROOT / "books/shin-yonenaga-white-candidates.json"
DEFAULT_OUTPUT = ROOT / "books/shin-yonenaga-white-book.txt"
MOVE_RE = re.compile(r"(?:[1-9][a-i][1-9][a-i]\+?|[PLNSGBR]\*[1-9][a-i])\Z")
ADOPTED = {"mainline", "reviewed_side_branch"}


def compile_book(source):
    data = json.loads(source.read_text(encoding="utf-8"))
    if data.get("side") != "white" or data.get("initial_position") != "startpos":
        raise ValueError("expected White candidates from startpos")

    lines = ["# Rakuyou Shin-Yonenaga-Gyoku White book v1",
             "# USI moves from startpos | White book move"]
    seen = {}
    adopted_count = 0
    for entry in data["entries"]:
        if entry["status"] not in ADOPTED:
            continue
        moves = entry["moves"]
        book_move = entry["book_move"]
        if not moves or len(moves) % 2 != 1:
            raise ValueError(f"{entry['id']}: expected a White-to-move position")
        if not all(isinstance(move, str) and MOVE_RE.fullmatch(move)
                   for move in moves + [book_move]):
            raise ValueError(f"{entry['id']}: invalid USI move")
        key = tuple(moves)
        if key in seen:
            raise ValueError(f"{entry['id']}: duplicate sequence with {seen[key]}")
        seen[key] = entry["id"]
        lines.append(f"# {entry['id']}")
        lines.append(f"{' '.join(moves)} | {book_move}")
        adopted_count += 1
    if not adopted_count:
        raise ValueError("no adopted book moves")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    book = compile_book(args.source)
    args.output.write_text(book, encoding="utf-8")
    count = sum(" | " in line for line in book.splitlines() if not line.startswith("#"))
    print(f"Wrote {args.output}: {count} positions")


if __name__ == "__main__":
    main()
