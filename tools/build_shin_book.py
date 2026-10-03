#!/usr/bin/env python3
"""Compile explicitly sided candidates into Rakuyou's small position book."""

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = ROOT / "books/shin-yonenaga-white-candidates.json"
DEFAULT_OUTPUT = ROOT / "books/shin-yonenaga-white-book.txt"
DEFAULT_EXPERIMENT_OUTPUT = ROOT / "books/shin-yonenaga-white-book-v2-experiment.txt"
MOVE_RE = re.compile(r"(?:[1-9][a-i][1-9][a-i]\+?|[PLNSGBR]\*[1-9][a-i])\Z")
ADOPTED = {"mainline", "reviewed_side_branch"}


def compile_book(source, extension=None, experimental=False, side="white"):
    if side not in {"white", "black"}:
        raise ValueError("expected side white or black")
    if experimental and extension is not None:
        raise ValueError("standalone experimental source cannot use an extension")
    sources = [source] + ([extension] if extension is not None else [])
    data_sources = [json.loads(path.read_text(encoding="utf-8")) for path in sources]
    for data in data_sources:
        if data.get("side") != side or data.get("initial_position") != "startpos":
            raise ValueError(f"expected {side.title()} candidates from startpos")

    version = ("standalone experiment" if experimental else
               "v2 experiment" if extension is not None else "v1")
    lines = [f"# Rakuyou Shin-Yonenaga-Gyoku {side.title()} book {version}",
             f"# USI moves from startpos | {side.title()} book move"]
    seen = {}
    adopted_count = 0
    for index, data in enumerate(data_sources):
        for entry in data["entries"]:
            status = entry["status"]
            if (index == 0 and status not in ADOPTED
                    and not (experimental and status == "experimental")):
                continue
            if index == 1 and status != "experimental":
                raise ValueError(f"{entry['id']}: expected an experimental extension")
            moves = entry["moves"]
            book_move = entry["book_move"]
            if not moves or len(moves) % 2 != (1 if side == "white" else 0):
                raise ValueError(f"{entry['id']}: expected a {side.title()}-to-move position")
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
    parser.add_argument("--source", type=Path)
    parser.add_argument("--side", choices=("white", "black"), default="white",
                        help="explicit candidate side; White remains the default")
    parser.add_argument("--extension", type=Path,
                        help="experimental entries to add without changing the first book")
    parser.add_argument("--experimental", action="store_true",
                        help="compile a standalone experimental source; requires explicit --output")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.side == "black":
        if not args.experimental or args.source is None or args.output is None:
            parser.error("--side black requires --source, --experimental and --output")
        protected = {path.resolve() for path in (ROOT / "books").glob("shin-yonenaga-white-*.txt")}
        if args.output.resolve() in protected:
            parser.error("a Black trial cannot overwrite an existing White book")
    if args.experimental and (args.extension is not None or args.output is None):
        parser.error("--experimental requires --output and cannot use --extension")
    output = args.output or (DEFAULT_EXPERIMENT_OUTPUT if args.extension else DEFAULT_OUTPUT)
    if args.experimental and output.resolve() in {
            DEFAULT_OUTPUT.resolve(), DEFAULT_EXPERIMENT_OUTPUT.resolve()}:
        parser.error("a standalone experiment cannot overwrite v1 or v2")
    if args.extension is not None and output.resolve() == DEFAULT_OUTPUT.resolve():
        parser.error("an experimental extension cannot overwrite the first book")
    book = compile_book(args.source or DEFAULT_SOURCE, args.extension, args.experimental,
                        side=args.side)
    output.write_text(book, encoding="utf-8")
    count = sum(" | " in line for line in book.splitlines() if not line.startswith("#"))
    print(f"Wrote {output}: {count} positions")


if __name__ == "__main__":
    main()
