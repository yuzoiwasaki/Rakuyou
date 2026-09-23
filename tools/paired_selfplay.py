#!/usr/bin/env python3
"""Run paired games between Shin-Yonenaga-Gyoku and normal Rakuyou."""

import argparse
import json
import queue
import re
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path


INFO_RE = re.compile(r"\bdepth (\d+).*?\bscore (cp|mate) ([^ ]+)(?:.*?\bpv (.*))?$")


class UsiEngine:
    def __init__(self, executable, shin_yonenaga_gyoku, own_book, threads, hash_mb,
                 book_file, book_max_ply):
        self.executable = executable.resolve()
        self.shin_yonenaga_gyoku = shin_yonenaga_gyoku
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
        self.send("setoption name ShinYonenagaGyoku value "
                  + ("true" if shin_yonenaga_gyoku else "false"))
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
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"Timed out waiting for {prefix}")
            try:
                line = self.lines.get(timeout=min(remaining, 1.0))
            except queue.Empty:
                if self.process.poll() is not None:
                    raise RuntimeError(f"Engine exited while waiting for {prefix}")
                continue
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
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                if self.process.poll() is None:
                    self.send("stop")
                raise TimeoutError("Timed out waiting for bestmove")
            try:
                line = self.lines.get(timeout=min(remaining, 1.0))
            except queue.Empty:
                if self.process.poll() is not None:
                    raise RuntimeError("Engine exited while waiting for bestmove")
                continue
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
    source_counts_by_player = {black_name: {}, white_name: {}}
    for record in records:
        source = record["source"]
        source_counts[source] = source_counts.get(source, 0) + 1
        player_counts = source_counts_by_player[record["player"]]
        player_counts[source] = player_counts.get(source, 0) + 1

    return {
        "black": black_name,
        "white": white_name,
        "result": result,
        "winner": winner,
        "reason": reason,
        "source_counts": source_counts,
        "source_counts_by_player": source_counts_by_player,
        "moves": moves,
        "records": records,
    }


def summarize(games):
    players = ("shin_yonenaga", "normal")
    summary = {
        "games_completed": len(games),
        "pairs_completed": len(games) // 2,
        "average_plies": 0.0,
        "reasons": {},
        "players": {},
    }
    for player in players:
        summary["players"][player] = {
            "wins": 0,
            "losses": 0,
            "draws": 0,
            "score": 0.0,
            "score_rate": 0.0,
            "by_color": {
                "black": {"wins": 0, "losses": 0, "draws": 0},
                "white": {"wins": 0, "losses": 0, "draws": 0},
            },
            "sources": {},
        }

    total_plies = 0
    for game in games:
        total_plies += len(game["records"])
        reason = game["reason"]
        summary["reasons"][reason] = summary["reasons"].get(reason, 0) + 1
        for player in players:
            stats = summary["players"][player]
            color = "black" if game["black"] == player else "white"
            color_stats = stats["by_color"][color]
            if game["winner"] == player:
                stats["wins"] += 1
                color_stats["wins"] += 1
            elif game["winner"] is None:
                stats["draws"] += 1
                color_stats["draws"] += 1
            else:
                stats["losses"] += 1
                color_stats["losses"] += 1
            for source, count in game["source_counts_by_player"][player].items():
                stats["sources"][source] = stats["sources"].get(source, 0) + count

    if games:
        summary["average_plies"] = round(total_plies / len(games), 2)
        for player in players:
            stats = summary["players"][player]
            stats["score"] = stats["wins"] + 0.5 * stats["draws"]
            stats["score_rate"] = round(stats["score"] / len(games), 4)
    return summary


def save_document(document, output):
    document["updated_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    document["summary"] = summarize(document["games"])
    document["summary"]["errors"] = len(document.get("errors", []))
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(output)


def format_duration(seconds):
    seconds = max(0, int(seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes}m {seconds}s"
    if minutes:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"


def parse_args():
    parser = argparse.ArgumentParser(
        description="新米長玉と通常のRakuyouを先後交代で2局対戦させます。")
    parser.add_argument("--engine", type=Path, default=Path("bin/release"))
    parser.add_argument("--depth", type=int, default=5)
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--hash", type=int, default=128, dest="hash_mb")
    parser.add_argument("--book-file", type=Path,
                        help="省略時はエンジン既定のbook.binを使う")
    parser.add_argument("--book-max-ply", type=int, default=20)
    parser.add_argument("--shin-book", choices=("off", "on"), default="off",
                        help="新米長玉側の定跡をオンまたはオフにする（通常側は常にオン）")
    parser.add_argument("--max-plies", type=int, default=256)
    parser.add_argument("--timeout", type=int, default=300,
                        help="1手の応答を待つ最大秒数")
    parser.add_argument("--pairs", type=int,
                        help="対局組数（1組は先後を交換した2局、既定値1）")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--resume", type=Path,
                        help="保存済みJSONの条件と結果を読み込んで再開する")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.resume is not None and args.output is not None:
        raise SystemExit("--resume and --output cannot be used together")

    if args.resume is not None:
        output = args.resume
        if not output.is_file():
            raise SystemExit(f"Resume file not found: {output}")
        document = json.loads(output.read_text())
        settings = document["settings"]
        requested_pairs = args.pairs or document["requested_pairs"]
        document["requested_pairs"] = requested_pairs
        engine_path = Path(settings["engine"])
        depth = settings["depth"]
        threads = settings["threads_per_engine"]
        hash_mb = settings["hash_mb_per_engine"]
        book_value = settings["book_file"]
        book_file = None if book_value == "book.bin" else Path(book_value)
        book_max_ply = settings["book_max_ply"]
        max_plies = settings["max_plies"]
        timeout = settings.get("timeout_seconds", 300)
        shin_book = settings["players"]["shin_yonenaga"]["OwnBook"]
    else:
        requested_pairs = args.pairs or 1
        engine_path = args.engine.resolve()
        depth = args.depth
        threads = args.threads
        hash_mb = args.hash_mb
        book_file = args.book_file.resolve() if args.book_file else None
        book_max_ply = args.book_max_ply
        max_plies = args.max_plies
        timeout = args.timeout
        shin_book = args.shin_book == "on"
        output = args.output or Path("results") / (
            "shin-book-" + args.shin_book + "-vs-normal-"
            + datetime.now().strftime("%Y%m%d-%H%M%S") + ".json"
        )
        settings = {
            "engine": str(engine_path),
            "depth": depth,
            "threads_per_engine": threads,
            "hash_mb_per_engine": hash_mb,
            "ponder": False,
            "book_file": str(book_file) if book_file else "book.bin",
            "book_max_ply": book_max_ply,
            "max_plies": max_plies,
            "timeout_seconds": timeout,
            "players": {
                "shin_yonenaga": {
                    "ShinYonenagaGyoku": True,
                    "OwnBook": shin_book,
                },
                "normal": {
                    "ShinYonenagaGyoku": False,
                    "OwnBook": True,
                },
            },
        }
        timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
        document = {
            "created_at": timestamp,
            "updated_at": timestamp,
            "requested_pairs": requested_pairs,
            "settings": settings,
            "games": [],
            "errors": [],
            "summary": summarize([]),
        }

    if not engine_path.is_file():
        raise SystemExit(f"Engine not found: {engine_path}")
    if (depth < 1 or threads < 1 or hash_mb < 1 or max_plies < 1
            or book_max_ply < 0 or timeout < 1 or requested_pairs < 1):
        raise SystemExit("numeric options are outside their supported range")
    if book_file is not None and not book_file.is_file():
        raise SystemExit(f"Book not found: {book_file}")
    total_games = requested_pairs * 2
    if len(document["games"]) > total_games:
        raise SystemExit("requested pairs are fewer than the games already saved")

    save_document(document, output)
    print(f"Results: {output}", flush=True)
    print(f"Progress: {len(document['games'])}/{total_games} games", flush=True)

    engines = {}
    run_started = time.monotonic()
    games_at_start = len(document["games"])
    interrupted = False
    try:
        engines["shin_yonenaga"] = UsiEngine(
            engine_path, True, shin_book, threads, hash_mb,
            book_file, book_max_ply)
        engines["normal"] = UsiEngine(
            engine_path, False, True, threads, hash_mb,
            book_file, book_max_ply)
        pairings = [("shin_yonenaga", "normal"), ("normal", "shin_yonenaga")]
        try:
            while len(document["games"]) < total_games:
                number = len(document["games"]) + 1
                pair_number = (number - 1) // 2 + 1
                game_in_pair = (number - 1) % 2 + 1
                black, white = pairings[game_in_pair - 1]
                print(f"Game {number}/{total_games} (pair {pair_number}/{requested_pairs}): "
                      f"black={black}, white={white}", flush=True)
                try:
                    game = play_game(engines, black, white, depth, max_plies, timeout)
                except Exception as error:
                    document.setdefault("errors", []).append({
                        "occurred_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                        "game": number,
                        "pair": pair_number,
                        "game_in_pair": game_in_pair,
                        "black": black,
                        "white": white,
                        "type": type(error).__name__,
                        "message": str(error),
                    })
                    save_document(document, output)
                    print(f"  error saved: {type(error).__name__}: {error}", flush=True)
                    raise
                game["pair"] = pair_number
                game["game_in_pair"] = game_in_pair
                document["games"].append(game)
                save_document(document, output)

                summary = document["summary"]
                shin = summary["players"]["shin_yonenaga"]
                completed_this_run = len(document["games"]) - games_at_start
                elapsed = time.monotonic() - run_started
                average = elapsed / completed_this_run
                remaining = average * (total_games - len(document["games"]))
                print(f"  {game['result']} ({game['reason']}), "
                      f"{len(game['records'])} plies", flush=True)
                print(f"  Shin: {shin['wins']}W {shin['losses']}L {shin['draws']}D, "
                      f"score {shin['score_rate']:.1%}", flush=True)
                print(f"  elapsed {format_duration(elapsed)}, "
                      f"ETA {format_duration(remaining)}", flush=True)
        except KeyboardInterrupt:
            interrupted = True
            print("Interrupted; completed games are saved.", flush=True)
    finally:
        for engine in engines.values():
            engine.close()

    save_document(document, output)
    if not interrupted:
        shin = document["summary"]["players"]["shin_yonenaga"]
        print(f"Completed: {shin['wins']}W {shin['losses']}L {shin['draws']}D, "
              f"score {shin['score_rate']:.1%}", flush=True)
    print(f"Saved: {output}", flush=True)


if __name__ == "__main__":
    main()
