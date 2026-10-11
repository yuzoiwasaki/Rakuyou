#!/usr/bin/env python3
"""Exclusive copy changing only selected king_safety opening/end int32 lanes."""
import hashlib
import math
import mmap
import shutil
import struct
from pathlib import Path
from prepare_learning_data import ROOT,digest
from king_safety_objective import vector


def validate_map(layout):
    if layout['bytes']!=259336912 or layout['scale']!=65536:raise ValueError('Unexpected safety ABI')
    begin,end=layout['begin'],layout['begin']+layout['table_bytes'];seen=set()
    for offset,mask in layout['entries']:
        if offset in seen or offset%16 or not begin<=offset<=end-16 or not 0<mask<16:
            raise ValueError('Invalid or duplicate safety entry')
        seen.add(offset)
    if not seen:raise ValueError('Empty safety entry map')


def protected_digest(path,entries):
    offsets=sorted(offset for offset,_ in entries);h=hashlib.sha256();index=0;start=0
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):
            b=bytearray(block);end=start+len(b)
            while index<len(offsets) and offsets[index]<end:
                offset=offsets[index]-start
                b[offset:offset+4]=b'\0'*4;b[offset+8:offset+12]=b'\0'*4;index+=1
            h.update(b);start=end
    return h.hexdigest()


def export(base,output,delta,expected_sha,layout):
    base,output=Path(base),Path(output)
    delta=vector(delta)
    if any(abs(x)>.5 for x in delta):raise ValueError('Safety coefficient limit exceeded')
    if output.resolve()==base.resolve() or output.resolve().is_relative_to((ROOT/'bin').resolve()):raise ValueError('Operational output forbidden')
    validate_map(layout)
    if digest(base)!=expected_sha:raise ValueError('Base SHA mismatch')
    raw=[math.trunc(x*65536) for x in delta]
    with base.open('rb') as src,output.open('xb') as dst:shutil.copyfileobj(src,dst)
    with output.open('r+b') as f:
        with mmap.mmap(f.fileno(),0) as data:
            for offset,mask in layout['entries']:
                for stage,lane in ((0,0),(1,2)):
                    inc=sum(raw[2*i+stage] for i in range(4) if mask & (1<<i))
                    value=struct.unpack_from('<i',data,offset+4*lane)[0]+inc
                    if not -(1<<31)<=value<(1<<31):raise ValueError('Safety int32 overflow')
                    struct.pack_into('<i',data,offset+4*lane,value)
    before=protected_digest(base,layout['entries']);after=protected_digest(output,layout['entries'])
    if before!=after or digest(base)!=expected_sha:raise ValueError('Protected bytes changed')
    return dict(candidate_sha256=digest(output),protected_sha256=before,delta=list(delta),raw_delta=raw,
                allowed_entries=len(layout['entries']),allowed_lanes=[0,2],base_sha256=expected_sha)
