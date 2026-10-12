#!/usr/bin/env python3
"""Exclusive candidate writer: copy a fixed base, alter only three tempo int32s."""

# Permit direct CLI execution as well as package imports.
import sys as _sys
from pathlib import Path as _RepoPath
if not __package__:
    _sys.path.insert(0, str(_RepoPath(__file__).resolve().parents[3]))
import hashlib
import json
import math
import shutil
import struct
import subprocess
from pathlib import Path

from tools.learning.data.prepare_learning_data import ROOT, digest
from tools.learning.core.tempo_objective import vector


def unchanged_digest(path,offset):
    h=hashlib.sha256()
    with Path(path).open("rb") as stream:
        left=offset
        while left:
            block=stream.read(min(left,1024*1024))
            if not block:raise ValueError("Truncated parameter file")
            h.update(block);left-=len(block)
        stream.seek(12,1)
        for block in iter(lambda:stream.read(1024*1024),b""):h.update(block)
    return h.hexdigest()


def export_candidate(base,output,delta_cp,expected_sha,probe):
    base,output,probe=Path(base),Path(output),Path(probe).resolve()
    delta=vector(delta_cp)
    if any(abs(v)>5 for v in delta):raise ValueError("Delta exceeds pilot 5cp bound")
    if output.resolve()==base.resolve() or output.resolve().is_relative_to((ROOT/"bin").resolve()):
        raise ValueError("Candidate must be separate from base and runtime bin directory")
    if digest(base)!=expected_sha:raise ValueError("Fixed-base SHA mismatch")
    layout=json.loads(subprocess.check_output([str(probe),"--layout"],text=True,timeout=30))
    info=json.loads(subprocess.check_output([str(probe),"--inspect-params",str(base.resolve())],text=True,timeout=30))
    size,offset,scale=(layout[k] for k in ("eval_parameters_bytes","tempo_offset","fv_scale"))
    if (size!=base.stat().st_size or not 0<=offset<=size-16 or offset%16 or
            layout["packed_score_bytes"]!=16 or scale!=65536 or info["fv_scale"]!=scale):
        raise ValueError("Unexpected native parameter layout")
    with base.open("rb") as stream:
        stream.seek(offset);raw=stream.read(16)
    orders=[order for order in ("<",">") if list(struct.unpack(order+"4i",raw))==info["tempo_raw"]]
    if len(orders)!=1:raise ValueError("Native byte order cannot be identified uniquely")
    order=orders[0]
    increments=[math.trunc(v*scale) for v in delta]
    changed=[v+i for v,i in zip(info["tempo_raw"][:3],increments)]
    if any(not -(1<<31)<=v<(1<<31) for v in changed):raise ValueError("Tempo int32 overflow")
    with base.open("rb") as src,output.open("xb") as dst:
        left=offset
        while left:
            block=src.read(min(left,1024*1024))
            if not block:raise ValueError("Base truncated during export")
            dst.write(block);left-=len(block)
        src.seek(12,1);dst.write(struct.pack(order+"3i",*changed))
        shutil.copyfileobj(src,dst)
    if output.stat().st_size!=size or digest(base)!=expected_sha:
        raise ValueError("Export size/base identity mismatch")
    before,after=unchanged_digest(base,offset),unchanged_digest(output,offset)
    if before!=after:raise ValueError("Non-tempo bytes changed")
    with output.open("rb") as stream:
        stream.seek(offset);exported=list(struct.unpack(order+"4i",stream.read(16)))
    if exported!=changed+[info["tempo_raw"][3]]:raise ValueError("Packed tempo mismatch")
    return dict(base_sha256=expected_sha,candidate_sha256=digest(output),
                delta_cp=list(delta),raw_increments=increments,tempo_raw_before=info["tempo_raw"],
                tempo_raw_after=exported,unchanged_regions_sha256=before,
                allowed_byte_offset=offset,allowed_byte_length=12,bytes=size,
                byte_order="little" if order=="<" else "big")
