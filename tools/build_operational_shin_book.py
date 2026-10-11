#!/usr/bin/env python3
"""Reproduce the first provisional combined Shin-Yonenaga-Gyoku book.

This composes the selected books without changing any position or move.
Engine integration tests, not this compiler, check full move legality.
"""

import argparse
from pathlib import Path

try:
    from .build_shin_book import compile_book
except ImportError:
    from build_shin_book import compile_book


ROOT = Path(__file__).resolve().parents[1]
BLACK_SOURCE = "books/shin-yonenaga-black-pawn76-right-side-experiment.json"
BLACK_BOOK = "books/shin-yonenaga-black-book-pawn76-right-side-experiment.txt"
WHITE_SOURCE = "books/shin-yonenaga-white-candidates.json"
WHITE_EXTENSION = "books/shin-yonenaga-white-v2-experiment.json"
WHITE_BOOK = "books/shin-yonenaga-white-book-v2-experiment.txt"
OUTPUT = ROOT / "books/shin-yonenaga-book-v1.txt"


def compile_operational_book(root=ROOT):
    selected = [
        (BLACK_BOOK, 6, compile_book(root / BLACK_SOURCE,
                                   experimental=True, side="black")),
        (WHITE_BOOK, 11, compile_book(root / WHITE_SOURCE,
                                    root / WHITE_EXTENSION)),
    ]
    lines = ["# Rakuyou Shin-Yonenaga-Gyoku provisional operational book v1",
             "# Black: pawn76 right-side six; White: unchanged v2 eleven",
             "# USI moves from startpos | book move (either side)"]
    seen = set()
    for name, expected, compiled in selected:
        if (root / name).read_text(encoding="utf-8") != compiled:
            raise ValueError(f"selected book differs from its source: {name}")
        rows = [line for line in compiled.splitlines()
                if line and not line.startswith("#")]
        if len(rows) != expected:
            raise ValueError(f"expected {expected} positions: {name}")
        for row in rows:
            parent = row.split(" | ", 1)[0]
            if parent in seen:
                raise ValueError(f"duplicate sequence: {parent}")
            seen.add(parent)
        lines.append(f"# Source: {name}")
        lines.extend(compiled.splitlines())
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="verify the committed combined file without writing")
    args = parser.parse_args()
    book = compile_operational_book()
    if args.check:
        if OUTPUT.read_text(encoding="utf-8") != book:
            parser.exit(1, "Combined book differs; regenerate it.\n")
        print("Combined book matches selected sources: 17 positions")
    else:
        OUTPUT.write_text(book, encoding="utf-8")
        print(f"Wrote {OUTPUT.relative_to(ROOT)}: 17 positions")


if __name__ == "__main__":
    main()
