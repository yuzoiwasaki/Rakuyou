#!/usr/bin/env python3
"""Check the experimental opening through USI: python3 tools/smoke_opening.py."""

import pathlib
import queue
import subprocess
import sys
import threading
import time


engine = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "bin/release").resolve()
process = subprocess.Popen(
    [str(engine)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT, text=True, bufsize=1,
)
output = queue.Queue()


def read_output():
    for line in process.stdout:
        output.put(line.rstrip())
    output.put(None)


threading.Thread(target=read_output, daemon=True).start()


def send(command):
    process.stdin.write(command + "\n")
    process.stdin.flush()


def receive(prefix, timeout=30):
    lines = []
    deadline = time.monotonic() + timeout
    while True:
        line = output.get(timeout=max(0.01, deadline - time.monotonic()))
        assert line is not None, "Engine exited: " + "\n".join(lines)
        lines.append(line)
        if line.startswith(prefix):
            return lines
        assert time.monotonic() < deadline, lines


def check(name, position, go, expected=None, opening=False, excluded=None):
    send(position)
    send(go)
    lines = receive("bestmove ")
    move = lines[-1].split()[1]
    assert expected is None or move == expected, (name, lines)
    assert move != excluded, (name, lines)
    assert any("Shin-Yonenaga opening:" in line for line in lines) == opening, (name, lines)
    if not opening:
        assert any(line.startswith("info depth ") for line in lines), (name, lines)
    print("PASS", name, move)


try:
    send("usi")
    receive("usiok")
    send("setoption name Threads value 1")
    send("setoption name USI_Hash value 16")
    send("isready")
    receive("readyok")
    send("usinewgame")
    check("Black opening", "position startpos", "go depth 1", "5i4h", True)
    for first in ("7g7f", "2g2f", "5i4h", "9i9h"):
        check("White after " + first, "position startpos moves " + first,
              "go depth 1", "5a6b", True)
    send("setoption name OwnBook value false")
    check("Opening without book", "position startpos", "go depth 1", "5i4h", True)
    check("Black normal search", "position startpos moves 5i4h 3c3d", "go depth 1")
    check("White normal search", "position startpos moves 7g7f 5a6b 2g2f", "go depth 1")
    check("searchmoves exclusion", "position startpos", "go depth 1 searchmoves 7g7f", "7g7f")
    check("ignoremoves exclusion", "position startpos", "go depth 1 ignoremoves 5i4h",
          excluded="5i4h")
    check("Custom SFEN", "position sfen lnsgkgsnl/1r5b1/ppppppppp/9/9/2P6/PP1PPPPPP/1B5R1/LNSGKGSNL w - 2",
          "go depth 1")
    for mode, release in (("infinite", "stop"), ("ponder", "ponderhit")):
        send("position startpos")
        send("go " + mode)
        receive("info string Shin-Yonenaga opening:")
        try:
            early = output.get(timeout=0.2)
        except queue.Empty:
            pass
        else:
            raise AssertionError(("Unexpected early output", early))
        send(release)
        assert receive("bestmove ")[-1].split()[1] == "5i4h"
        print("PASS", mode, "waits for", release)
finally:
    if process.poll() is None:
        send("quit")
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
