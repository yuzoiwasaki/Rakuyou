#!/usr/bin/env python3
"""Check prepared source hashes against archived reports, without promoting data.

Report mentions corroborate saved raw data. They do not reconstruct historical
runtime parameters or certify which binary generated an individual game.
"""
import argparse
import hashlib
import json
from pathlib import Path

from prepare_learning_data import ROOT, digest


# These report rows use short run labels rather than complete JSON filenames.
SHORT_LABELS = {
    "shin-black-pawn26-trial-r1-depth15-50games.json": (
        "docs/experiments/books/black/2026-10-03-black-300-game-branch-review.md", "trial-r1"),
    "shin-black-pawn26-trial-r2-depth15-50games.json": (
        "docs/experiments/books/black/2026-10-03-black-300-game-branch-review.md", "trial-r2"),
}


def references(source, reports):
    name = Path(source["path"]).name
    refs = []
    for path, content in sorted(reports.items()):
        lines = content.splitlines()
        for i, line in enumerate(lines):
            label = name
            if name in SHORT_LABELS and path == SHORT_LABELS[name][0]:
                label = "`" + SHORT_LABELS[name][1] + "`"
            if label not in line:
                continue
            # A table row, or a filename followed by its SHA in the next 3 lines.
            window = "\n".join(lines[i:i+4])
            if source["sha256"] not in window:
                continue
            refs.append({"path": path, "line": i+1,
                         "label": label, "report_sha256": hashlib.sha256(content.encode()).hexdigest()})
    return refs


def audit(manifest_path, root=ROOT):
    raw = Path(manifest_path).read_bytes()
    manifest = json.loads(raw)
    reports = {p.relative_to(root).as_posix(): p.read_text()
               for p in sorted((root / "docs/experiments").rglob("*.md"))
               if "learning" not in p.name}
    runs = []
    for source in manifest["sources"]:
        if source.get("excluded"):
            continue
        path = root / source["path"]
        if not path.resolve().is_relative_to(root.resolve()):
            raise ValueError("Source outside repository")
        actual = digest(path)
        if actual != source["sha256"]:
            raise ValueError("Prepared source changed: " + source["path"])
        refs = references(source, reports)
        runs.append({"path": source["path"], "sha256": actual,
                     "games": source["games"], "report_references": refs,
                     "raw_data_status": "corroborated_by_report" if refs else "not_corroborated",
                     "historical_runtime_hashes": {
                         "params.bin": None, "progress.bin": None, "probability.bin": None},
                     "training_ready": False})
    outputs = {}
    for name, record in manifest["outputs"].items():
        path = Path(manifest_path).parent / record["path"]
        if not path.resolve().is_relative_to(Path(manifest_path).parent.resolve()):
            raise ValueError("Split output outside preparation directory")
        if digest(path) != record["sha256"]:
            raise ValueError("Prepared split changed: " + name)
        outputs[name] = {"sha256": record["sha256"], "positions": record["positions"]}
    return {"schema": "rakuyou-learning-provenance-v1",
            "preparation_manifest_sha256": hashlib.sha256(raw).hexdigest(),
            "tool_sha256": digest(Path(__file__)),
            "runs": runs, "run_count": len(runs),
            "corroborated_runs": sum(bool(r["report_references"]) for r in runs),
            "games": sum(r["games"] for r in runs), "split_outputs": outputs,
            "training_ready": False,
            "limits": ["report hash correspondence is not a historical runtime hash",
                       "current runtime hashes cannot fill historical missing values",
                       "formal outcome adjudication and long-prefix correlation remain pending"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(args.manifest)
    if args.output:
        with args.output.open("x") as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
