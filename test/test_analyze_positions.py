#!/usr/bin/env python3
"""Test position-analysis engine lifecycle without running a real engine."""

import contextlib
import io
import json
import sys
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import analyze_positions


class EngineLifecycleTest(unittest.TestCase):
    def run_analysis(self, fresh, engines):
        source = Mock()
        source.read_text.return_value = json.dumps({"positions": [
            {"id": "first", "moves": []},
            {"id": "second", "moves": []},
        ]})
        args = Namespace(
            engine=Path(__file__), positions=source, output=Path("unused.json"),
            depth=1, multipv=1, threads=1, hash_mb=1, timeout=30,
            stop_after=None, shin_yonenaga_gyoku="on", fresh_engine=fresh,
        )
        with patch.object(analyze_positions, "parse_args", return_value=args), \
                patch.object(analyze_positions, "Engine", side_effect=engines) as factory, \
                patch.object(analyze_positions, "save"), \
                contextlib.redirect_stdout(io.StringIO()):
            analyze_positions.main()
        return factory

    def make_engine(self):
        engine = Mock()
        engine.analyze.return_value = {
            "candidates": [], "elapsed_seconds": 0,
        }
        return engine

    def test_default_reuses_engine(self):
        engine = self.make_engine()
        factory = self.run_analysis(False, [engine])
        self.assertEqual(factory.call_count, 1)
        self.assertEqual(engine.analyze.call_count, 2)
        engine.close.assert_called_once_with()

    def test_fresh_restarts_engine_for_each_position(self):
        engines = [self.make_engine(), self.make_engine()]
        factory = self.run_analysis(True, engines)
        self.assertEqual(factory.call_count, 2)
        for engine in engines:
            engine.analyze.assert_called_once()
            engine.close.assert_called_once_with()

    def test_fresh_closes_engine_on_error(self):
        engine = self.make_engine()
        engine.analyze.side_effect = RuntimeError("search failed")
        with self.assertRaisesRegex(RuntimeError, "search failed"):
            self.run_analysis(True, [engine])
        engine.close.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
