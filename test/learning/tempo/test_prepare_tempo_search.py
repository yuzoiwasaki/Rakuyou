#!/usr/bin/env python3
"""Verify independent runtime copies and previously diagnosed root selection."""

# Permit direct CLI execution as well as package imports.
import sys as _sys
from pathlib import Path as _RepoPath
if not __package__:
    _sys.path.insert(0, str(_RepoPath(__file__).resolve().parents[3]))
import sys
import tempfile
import unittest
from pathlib import Path
from tools.learning.tempo.prepare_tempo_search import copy_verified, select_positions
from tools.learning.data.prepare_learning_data import digest


class SearchPreparationTest(unittest.TestCase):
    def test_independent_copy_and_existing_output_refusal(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'source';target=Path(d)/'copy'
            source.write_bytes(b'params')
            copy_verified(source,target,digest(source))
            target.write_bytes(b'changed')
            self.assertEqual(source.read_bytes(),b'params')
            with self.assertRaises(FileExistsError):copy_verified(source,target,digest(source))

    def test_wrong_sha_does_not_create_copy(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'source';target=Path(d)/'copy';source.write_bytes(b'params')
            with self.assertRaises(ValueError):copy_verified(source,target,'wrong')
            self.assertFalse(target.exists())

    def inputs(self):
        parts={};review={'records':{}}
        for split in ('validation','test'):
            parts[split]=[dict(id=split+str(i),run=split,sfen=str(i),stratum=str(i),moves_before=[]) for i in range(6)]
            review['records'][split]=[dict(id=r['id'],run=r['run'],stratum=r['stratum'],base={'root_sfen':r['sfen']}) for r in parts[split]]
        return parts,review

    def test_only_diagnosed_roots_selected(self):
        parts,review=self.inputs()
        parts['test'].append(dict(id='unseen'))
        selected=select_positions(parts,review)
        self.assertEqual(len(selected),12)
        self.assertNotIn('unseen',[r['id'] for r in selected])

    def test_mismatched_review_rejected(self):
        parts,review=self.inputs();review['records']['test'][0]['base']['root_sfen']='wrong'
        with self.assertRaises(ValueError):select_positions(parts,review)


if __name__=='__main__':unittest.main()
