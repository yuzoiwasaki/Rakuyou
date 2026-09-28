#!/usr/bin/env python3

"""Analyze selected start-position move sequences with Rakuyou MultiPV."""

import argparse
import json
import queue
import re
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path


FIELD_PATTERNS = {
    "depth": re.compile(r"\bdepth (\d+)"),
    "seldepth": re.compile(r"\bseldepth (\d+)"),
    "multipv": re.compile(r"\bmultipv (\d+)"),
    "score": re.compile(r"\bscore (cp|mate) ([^ ]+)"),
    "nodes": re.compile(r"\bnodes (\d+)"),
    "time_ms": re.compile(r"\btime (\d+)"),
    "pv": re.compile(r"\bpv(?: (.*))?$"),
}


def parse_info(line):
    matches = {name: pattern.search(line) for name, pattern in FIELD_PATTERNS.items()}
    if not matches["depth"] or not matches["score"] or not matches["pv"]:
        return None
    return {
        "depth": int(matches["depth"].group(1)),
        "seldepth": int(matches["seldepth"].group(1)) if matches["seldepth"] else None,
        "multipv": int(matches["multipv"].group(1)) if matches["multipv"] else 1,
        "score_type": matches["score"].group(1),
        "score": matches["score"].group(2),
        "nodes": int(matches["nodes"].group(1)) if matches["nodes"] else None,
        "time_ms": int(matches["time_ms"].group(1)) if matches["time_ms"] else None,
        "pv": matches["pv"].group(1).split() if matches["pv"].group(1) else [],
        "raw": line,
    }


class Engine:
    def __init__(self, executable, threads, hash_mb, multipv,
                 shin_yonenaga_gyoku):
        self.executable = executable.resolve()
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
        options = {
            "ShinYonenagaGyoku": "true" if shin_yonenaga_gyoku else "false",
            "OwnBook": "false",
            "Threads": str(threads),
            "USI_Hash": str(hash_mb),
            "USI_Ponder": "false",
            "MultiPV": str(multipv),
        }
        for name, value in options.items():
            self.send(f"setoption name {name} value {value}")
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

    def analyze(self, moves, depth, timeout, searchmoves=None, stop_after=None,
                multipv=1):
        self.send("usinewgame")
        position = "position startpos"
        if moves:
            position += " moves " + " ".join(moves)
        self.send(position)
        go_command = f"go depth {depth}"
        if searchmoves:
            go_command += " searchmoves " + " ".join(searchmoves)
        self.send(go_command)
        latest = {}
        by_depth = {}
        started = time.monotonic()
        deadline = started + timeout
        stopped_early = False
        while True:
            if (stop_after is not None and not stopped_early
                    and time.monotonic() - started >= stop_after):
                self.send("stop")
                stopped_early = True
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
                info = parse_info(line)
                if info:
                    latest[info["multipv"]] = info
                    by_depth.setdefault(info["depth"], {})[info["multipv"]] = info
            elif line.startswith("bestmove "):
                if stopped_early:
                    complete_depths = [
                        current_depth for current_depth, candidates in by_depth.items()
                        if all(rank in candidates for rank in range(1, multipv + 1))
                    ]
                    if not complete_depths:
                        raise RuntimeError("No complete MultiPV depth before stop")
                    candidates = by_depth[max(complete_depths)]
                else:
                    candidates = latest
                return {
                    "bestmove": line.split()[1],
                    "elapsed_seconds": round(time.monotonic() - started, 3),
                    "stopped_early": stopped_early,
                    "candidates": [candidates[key] for key in sorted(candidates)],
                }

    def close(self):
        if self.process.poll() is None:
            self.send("quit")
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.terminate()


def save(document, output):
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    document["updated_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    temporary.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(output)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("positions", type=Path, help="JSON file containing named move sequences")
    parser.add_argument("--engine", type=Path, default=Path("bin/release"))
    parser.add_argument("--depth", type=int, default=20)
    parser.add_argument("--multipv", type=int, default=3)
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--hash", type=int, default=512, dest="hash_mb")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--stop-after", type=int,
                        help="stop a long search after this many seconds and save its last complete MultiPV depth")
    parser.add_argument("--shin-yonenaga-gyoku", choices=("on", "off"), default="on",
                        help="enable or disable the ShinYonenagaGyoku evaluation")
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    if not args.engine.is_file():
        raise SystemExit(f"Engine not found: {args.engine}")
    if min(args.depth, args.multipv, args.threads, args.hash_mb, args.timeout) < 1:
        raise SystemExit("numeric options must be positive")
    if args.stop_after is not None and not 0 < args.stop_after < args.timeout:
        raise SystemExit("--stop-after must be positive and less than --timeout")
    source = json.loads(args.positions.read_text(encoding="utf-8"))
    positions = source.get("positions", [])
    if not positions:
        raise SystemExit("positions file contains no positions")
    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    shin_yonenaga_gyoku = args.shin_yonenaga_gyoku == "on"
    document = {
        "created_at": timestamp,
        "updated_at": timestamp,
        "position_source": str(args.positions),
        "settings": {
            "engine": str(args.engine.resolve()),
            "depth": args.depth,
            "multipv": args.multipv,
            "threads": args.threads,
            "hash_mb": args.hash_mb,
            "timeout_seconds": args.timeout,
            "stop_after_seconds": args.stop_after,
            "ShinYonenagaGyoku": shin_yonenaga_gyoku,
            "OwnBook": False,
            "Ponder": False,
        },
        "positions": [],
        "errors": [],
    }
    save(document, args.output)
    engine = None
    try:
        engine = Engine(
            args.engine, args.threads, args.hash_mb, args.multipv,
            shin_yonenaga_gyoku,
        )
        for index, position in enumerate(positions, 1):
            print(f"[{index}/{len(positions)}] {position['id']}", flush=True)
            try:
                result = engine.analyze(
                    position.get("moves", []), args.depth, args.timeout,
                    position.get("searchmoves"), args.stop_after, args.multipv,
                )
                document["positions"].append({**position, "analysis": result})
                save(document, args.output)
                candidates = result["candidates"]
                summary = " ".join(
                    f"{candidate['multipv']}:{candidate['score_type']} {candidate['score']}"
                    for candidate in candidates
                )
                print(f"  {summary} ({result['elapsed_seconds']}s)", flush=True)
            except Exception as error:
                document["errors"].append({"id": position["id"], "error": str(error)})
                save(document, args.output)
                raise
    finally:
        if engine is not None:
            engine.close()
    print(f"Results: {args.output}")


if __name__ == "__main__":
    main()
