#!/usr/bin/env python3
"""Archived SHA correspondence must not invent historical parameter identity."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from audit_learning_provenance import audit, references


class ProvenanceTest(unittest.TestCase):
    def test_report_filename_and_hash_must_be_nearby(self):
        s = dict(path="results/game.json", sha256="a"*64)
        self.assertTrue(references(s, {"report.md": "`game.json`\nSHA: " + "a"*64}))
        self.assertFalse(references(s, {"report.md": "`game.json`\n" + "\n"*4 + "a"*64}))
        self.assertFalse(references(s, {"report.md": "`other.json` " + "a"*64}))

    def test_short_label_only_matches_its_specific_report(self):
        s = dict(path="results/shin-black-pawn26-trial-r1-depth15-50games.json", sha256="b"*64)
        line = "| `trial-r1` | `" + "b"*64 + "` |"
        self.assertFalse(references(s, {"other.md": line}))
        self.assertTrue(references(s, {"docs/experiments/books/black/2026-10-03-black-300-game-branch-review.md": line}))

    def test_changed_source_rejected_and_runtime_stays_unknown(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/"results").mkdir()
            (root/"docs/experiments").mkdir(parents=True)
            source = root/"results/game.json"
            source.write_text("{}")
            sha = hashlib.sha256(source.read_bytes()).hexdigest()
            (root/"docs/experiments/report.md").write_text("`game.json` " + sha)
            m = dict(sources=[dict(path="results/game.json", sha256=sha, games=1)], outputs={})
            manifest = root/"manifest.json"
            manifest.write_text(json.dumps(m))
            result = audit(manifest, root)
            self.assertEqual(result["corroborated_runs"], 1)
            self.assertFalse(result["training_ready"])
            self.assertTrue(all(v is None for v in result["runs"][0]["historical_runtime_hashes"].values()))
            source.write_text("changed")
            with self.assertRaises(ValueError):
                audit(manifest, root)

    def test_nested_report_is_discovered(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/"results").mkdir()
            reports = root/"docs/experiments/books/white"
            reports.mkdir(parents=True)
            source = root/"results/game.json"
            source.write_text("{}")
            sha = hashlib.sha256(source.read_bytes()).hexdigest()
            (reports/"report.md").write_text("`game.json` " + sha)
            manifest = root/"manifest.json"
            manifest.write_text(json.dumps(dict(sources=[dict(path="results/game.json", sha256=sha, games=1)], outputs={})))
            result = audit(manifest, root)
            self.assertEqual(result["corroborated_runs"], 1)
            self.assertEqual(result["runs"][0]["report_references"][0]["path"],
                             "docs/experiments/books/white/report.md")
            self.assertFalse(result["training_ready"])

    def test_changed_split_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/"docs/experiments").mkdir(parents=True)
            (root/"train.jsonl").write_text("changed")
            m = dict(sources=[], outputs={"train": dict(path="train.jsonl", sha256="c"*64, positions=1)})
            manifest = root/"manifest.json"
            manifest.write_text(json.dumps(m))
            with self.assertRaises(ValueError):
                audit(manifest, root)


if __name__ == "__main__":
    unittest.main()
