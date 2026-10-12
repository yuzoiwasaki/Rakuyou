#!/usr/bin/env python3
"""Verified, exclusive local copies. No hard links, deletion or external upload."""

# Permit direct CLI execution as well as package imports.
import sys as _sys
from pathlib import Path as _RepoPath
if not __package__:
    _sys.path.insert(0, str(_RepoPath(__file__).resolve().parents[3]))
import json
import shutil
from pathlib import Path

from tools.learning.data.prepare_learning_data import ROOT, digest


def safe_path(root,name):
    p=Path(name)
    if p.is_absolute() or ".." in p.parts or not (root/p).resolve().is_relative_to(root.resolve()):
        raise ValueError("Backup path escapes root")
    return root/p


def create_backup(paths,output,root=ROOT):
    root,output=Path(root),Path(output)
    if output.resolve().is_relative_to((root/"bin").resolve()):raise ValueError("Runtime backup output forbidden")
    names=sorted(set(paths))
    if not names:raise ValueError("Empty backup")
    output.mkdir(parents=True,exist_ok=False)
    entries=[]
    for name in names:
        source=safe_path(root,name)
        sha=digest(source)
        target=safe_path(output,"files/"+name)
        target.parent.mkdir(parents=True,exist_ok=True)
        with source.open("rb") as src,target.open("xb") as dst:shutil.copyfileobj(src,dst)
        if digest(target)!=sha or digest(source)!=sha or source.stat().st_ino==target.stat().st_ino:
            raise ValueError("Backup identity/hash mismatch: "+name)
        entries.append(dict(source=name,copy="files/"+name,sha256=sha,bytes=source.stat().st_size))
    result=dict(schema="rakuyou-learning-backup-v1",kind="local same-volume independent copies",
                external_backup=False,files=entries)
    with (output/"manifest.json").open("x") as stream:
        json.dump(result,stream,ensure_ascii=False,sort_keys=True,indent=2);stream.write("\n")
    return result


def verify_backup(manifest,required=None,root=ROOT):
    manifest,root=Path(manifest),Path(root)
    data=json.loads(manifest.read_bytes())
    if data.get("schema")!="rakuyou-learning-backup-v1" or not data.get("files"):
        raise ValueError("Invalid backup manifest")
    seen={}
    for record in data["files"]:
        name=record["source"]
        if name in seen or record["copy"]!="files/"+name:raise ValueError("Duplicate/invalid backup mapping")
        source=safe_path(root,name);copy=safe_path(manifest.parent,record["copy"])
        if (digest(copy)!=record["sha256"] or digest(source)!=record["sha256"] or
                copy.stat().st_size!=record["bytes"] or source.stat().st_ino==copy.stat().st_ino):
            raise ValueError("Backup/source changed: "+name)
        seen[name]=record["sha256"]
    for name,sha in (required or {}).items():
        if seen.get(name)!=sha:raise ValueError("Required backup missing/mismatched: "+name)
    return seen
