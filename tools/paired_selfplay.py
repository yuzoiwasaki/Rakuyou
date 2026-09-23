#!/usr/bin/env python3
"""Run two paired Rakuyou games with OwnBook enabled and disabled."""

import argparse
import json
import queue
import re
import subprocess
import threading
from datetime import datetime
from pathlib import Path


INFO_RE = re.compile(r"\bdepth (\d+).*?\bscore (cp|mate) ([^ ]+)(?:.*?\bpv (.*))?$")


class UsiEngine:
    def __init__(self, executable, own_book, threads, hash_mb,
                 book_file, book_max_ply):
        self.executable = executable.resolve()
        self.own_book = own_book
        self.lines = queue.Queue()
        self.process = subprocess.Popen(
            [str(self.executable)],
            cwd=str(self.executable.parent),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        threading.Thread(target=self._read_output, daemon=True).start()
        self.send("usi")
        self.wait_for("usiok", 10)
        self.send("setoption name OwnBook value " + ("true" if own_book else "false"))
        self.send(f"setoption name Threads value {threads}")
        self.send(f"setoption name USI_Hash value {hash_mb}")
        self.send("setoption name USI_Ponder value false")
        if book_file is not None:
            self.send(f"setoption name BookFile value {book_file.resolve()}")
        self.send(f"setoption name BookMaxPly value {book_max_ply}")
        self.send("isready")
        self.wait_for("readyok", 30)

    def _read_output(self):
        for line in self.process.stdout:
            self.lines.put(line.rstrip("\n"))

    def send(self, command):
        if self.process.poll() is not None:
            raise RuntimeError(f"Engine exited before command: {command}")
        self.process.stdin.write(command + "\n")
        self.process.stdin.flush()

    def wait_for(self, prefix, timeout):
        while True:
            try:
                line = self.lines.get(timeout=timeout)
            except queue.Empty:
                raise TimeoutError(f"Timed out waiting for {prefix}")
            if line.startswith(prefix):
                return line

    def new_game(self):
        self.send("usinewgame")

    def choose_move(self, moves, depth, timeout):
        position = "position startpos"
        if moves:
            position += " moves " + " ".join(moves)
        self.send(position)
        self.send(f"go depth {depth}")

        latest_info = None
        source = "search"
        while True:
            try:
                line = self.lines.get(timeout=timeout)
            except queue.Empty:
                self.send("stop")
                raise TimeoutError("Timed out waiting for bestmove")
            if line.startswith("info "):
                if "Shin-Yonenaga-Gyoku opening:" in line:
                    source = "fixed_opening"
                elif line.startswith("info time 0 depth "):
                    source = "book"
                match = INFO_RE.search(line)
                if match:
                    latest_info = {
                        "depth": int(match.group(1)),
                        "score_type": match.group(2),
                        "score": match.group(3),
                        "pv": match.group(4).split() if match.group(4) else [],
                        "raw": line,
                    }
            elif line.startswith("bestmove "):
                return line.split()[1], latest_info, source

    def gameover(self, result):
        self.send(f"gameover {result}")

    def close(self):
        if self.process.poll() is None:
            self.send("quit")
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.terminate()


def play_game(engines, black_name, white_name, depth, max_plies, timeout):
    for engine in engines.values():
        engine.new_game()

    moves = []
    records = []
    sides = {"black": black_name, "white": white_name}
    result = "draw"
    reason = "max_plies"

    for ply in range(1, max_plies + 1):
        color = "black" if ply % 2 else "white"
        player = sides[color]
        move, info, source = engines[player].choose_move(moves, depth, timeout)
        records.append({
            "ply": ply,
            "color": color,
            "player": player,
            "move": move,
            "source": source,
            "analysis": info,
        })

        if move == "resign":
            result = "white_win" if color == "black" else "black_win"
            reason = "resign"
            break
        if move == "win":
            result = "black_win" if color == "black" else "white_win"
            reason = "declaration"
            break
        moves.append(move)

    winner = None
    if result == "black_win":
        winner = black_name
    elif result == "white_win":
        winner = white_name

    for name, engine in engines.items():
        engine.gameover("draw" if winner is None else ("win" if name == winner else "lose"))

    source_counts = {}
    for record in records:
        source = record["source"]
        source_counts[source] = source_counts.get(source, 0) + 1

    return {
        "black": black_name,
        "white": white_name,
        "result": result,
        "winner": winner,
        "reason": reason,
        "source_counts": source_counts,
        "moves": moves,
        "records": records,
    }


def parse_args():
    parser = argparse.ArgumentParser(description="定跡オン・オフを先後交代で2局対戦させます。")
    parser.add_argument("--engine", type=Path, default=Path("bin/release"))
    parser.add_argument("--depth", type=int, default=5)
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--hash", type=int, default=128, dest="hash_mb")
    parser.add_argument("--book-file", type=Path,
                        help="省略時はエンジン既定のbook.binを使う")
    parser.add_argument("--book-max-ply", type=int, default=20)
    parser.add_argument("--max-plies", type=int, default=256)
    parser.add_argument("--timeout", type=int, default=300,
                        help="1手の応答を待つ最大秒数")
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main():
    args = parse_args()
    if not args.engine.is_file():
        raise SystemExit(f"Engine not found: {args.engine}")
    if (args.depth < 1 or args.threads < 1 or args.hash_mb < 1
            or args.max_plies < 1 or args.book_max_ply < 0):
        raise SystemExit("numeric options are outside their supported range")
    if args.book_file is not None and not args.book_file.is_file():
        raise SystemExit(f"Book not found: {args.book_file}")

    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    output = args.output or Path("results") / (
        "book-on-vs-off-" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".json"
    )
    settings = {
        "engine": str(args.engine.resolve()),
        "depth": args.depth,
        "threads_per_engine": args.threads,
        "hash_mb_per_engine": args.hash_mb,
        "ponder": False,
        "book_file": str(args.book_file.resolve()) if args.book_file else "book.bin",
        "book_max_ply": args.book_max_ply,
        "max_plies": args.max_plies,
    }

    engines = {}
    try:
        engines["book_on"] = UsiEngine(
            args.engine, True, args.threads, args.hash_mb,
            args.book_file, args.book_max_ply)
        engines["book_off"] = UsiEngine(
            args.engine, False, args.threads, args.hash_mb,
            args.book_file, args.book_max_ply)
        pairings = [("book_on", "book_off"), ("book_off", "book_on")]
        games = []
        for number, (black, white) in enumerate(pairings, 1):
            print(f"Game {number}: black={black}, white={white}", flush=True)
            game = play_game(engines, black, white, args.depth, args.max_plies, args.timeout)
            games.append(game)
            print(f"  {game['result']} ({game['reason']}), {len(game['moves'])} moves", flush=True)
            print(f"  sources: {game['source_counts']}", flush=True)
    finally:
        for engine in engines.values():
            engine.close()

    document = {"created_at": timestamp, "settings": settings, "games": games}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n")
    print(f"Saved: {output}")


if __name__ == "__main__":
    main()
