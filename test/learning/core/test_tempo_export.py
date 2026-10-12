#!/usr/bin/env python3
"""Candidate file isolation, byte preservation and malformed export rejection."""

# Permit direct CLI execution as well as package imports.
import sys as _sys
from pathlib import Path as _RepoPath
if not __package__:
    _sys.path.insert(0, str(_RepoPath(__file__).resolve().parents[3]))
import hashlib
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.learning.core.tempo_export import export_candidate


class ExportTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.base=self.root/"base.bin";self.out=self.root/"candidate.bin"
        self.raw=[-123,234,-345,999]
        self.base.write_bytes(b"a"*64+struct.pack("<4i",*self.raw)+b"z"*48)
        self.sha=hashlib.sha256(self.base.read_bytes()).hexdigest()
        def native(args,**kwargs):
            if args[1]=="--layout":return json.dumps(dict(eval_parameters_bytes=128,tempo_offset=64,packed_score_bytes=16,fv_scale=65536))
            return json.dumps(dict(tempo_raw=self.raw,fv_scale=65536))
        mock=patch("tools.learning.core.tempo_export.subprocess.check_output",side_effect=native)
        mock.start();self.addCleanup(mock.stop)

    def test_only_three_tempo_entries_change(self):
        r=export_candidate(self.base,self.out,(.25,-.5,.75),self.sha,"probe")
        a,b=self.base.read_bytes(),self.out.read_bytes()
        self.assertEqual(a[:64]+a[76:],b[:64]+b[76:])
        self.assertEqual(r["tempo_raw_after"],[-123+16384,234-32768,-345+49152,999])
        self.assertEqual(hashlib.sha256(a).hexdigest(),self.sha)

    def test_zero_delta_preserves_all_bytes(self):
        export_candidate(self.base,self.out,(0,0,0),self.sha,"probe")
        self.assertEqual(self.base.read_bytes(),self.out.read_bytes())

    def test_existing_output_or_same_base_is_rejected(self):
        self.out.write_bytes(b"keep")
        with self.assertRaises(FileExistsError):export_candidate(self.base,self.out,(0,0,0),self.sha,"probe")
        self.assertEqual(self.out.read_bytes(),b"keep")
        with self.assertRaises(ValueError):export_candidate(self.base,self.base,(0,0,0),self.sha,"probe")

    def test_bad_delta_or_base_identity_rejected_before_creation(self):
        for d in ((6,0,0),(float("nan"),0,0),(True,0,0)):
            with self.assertRaises(ValueError):export_candidate(self.base,self.out,d,self.sha,"probe")
        with self.assertRaises(ValueError):export_candidate(self.base,self.out,(0,0,0),"wrong","probe")
        self.assertFalse(self.out.exists())

    def test_int32_overflow_rejected(self):
        self.raw[0]=(1<<31)-1
        self.base.write_bytes(b"a"*64+struct.pack("<4i",*self.raw)+b"z"*48)
        self.sha=hashlib.sha256(self.base.read_bytes()).hexdigest()
        with self.assertRaises(ValueError):export_candidate(self.base,self.out,(1,0,0),self.sha,"probe")
        self.assertFalse(self.out.exists())


if __name__=="__main__":unittest.main()
