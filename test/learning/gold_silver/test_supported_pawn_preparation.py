import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from tools.learning.gold_silver import supported_pawn_preparation as prep


def sfen(pieces):
    pieces={'9a':'k','1i':'K',**pieces}
    rows=[]
    for rank in 'abcdefghi':
        row='';empty=0
        for file in range(9,0,-1):
            piece=pieces.get(str(file)+rank)
            if piece:
                row+=(str(empty) if empty else '')+piece;empty=0
            else:empty+=1
        rows.append(row+(str(empty) if empty else ''))
    return '/'.join(rows)+' b - 1'


def rotated(pieces):
    return {str(10-int(s[0]))+chr(ord('a')+ord('i')-ord(s[1])):p.swapcase()
            for s,p in pieces.items()}


class SupportedPawnTests(unittest.TestCase):
    def test_geometry_scope_and_color_symmetry_match_native(self):
        cases=[
            ({'5e':'P','5f':'S','4f':'G'},1), # two defenders, one pawn
            ({'3e':'P','3f':'S','7e':'P','7f':'G'},2), # boundary files included
            ({'1e':'P','1f':'S','2e':'P','2f':'G'},0), # outside central files
            ({'5e':'+P','5f':'S'},0), # promoted pawn excluded
            ({'5e':'P','5f':'+S'},0), # promoted silver excluded
            ({'5e':'P','4e':'G'},1), # lateral gold support
            ({'5e':'P','4e':'S'},0), # nearby silver with no actual control
            ({'5e':'P','5d':'S'},0), # backward straight silver excluded
            ({'5d':'P','5e':'S'},0), # non-fifth-rank pawn excluded
        ]
        positions=[];expected=[]
        for pieces,count in cases:
            positions.extend([sfen(pieces),sfen(rotated(pieces))])
            expected.extend([dict(black=count,white=0),dict(black=0,white=count)])
        self.assertEqual([prep.independent_counts(p) for p in positions],expected)
        run=subprocess.run([str(prep.PROBE),'--pawn-sfen',str(prep.ROOT/'bin/params.bin')],
                           input='\n'.join(positions)+'\n',text=True,capture_output=True,timeout=30,check=True)
        self.assertEqual([json.loads(line)['supported_pawn_counts'] for line in run.stdout.splitlines()],expected)

    def test_modified_source_rejected_before_native_or_output(self):
        with patch.object(prep,'digest',return_value='changed'),patch.object(prep,'SupportedPawnProbe') as native:
            with self.assertRaisesRegex(ValueError,'Bound input changed'):
                prep.verify_inputs()
            native.assert_not_called()

    def test_output_exclusivity_and_runtime_path_guard(self):
        with tempfile.TemporaryDirectory(dir=prep.ROOT/'results') as directory:
            with patch.object(prep,'verify_inputs') as inputs:
                with self.assertRaisesRegex(ValueError,'new results directory'):
                    prep.run(Path(directory))
                with self.assertRaisesRegex(ValueError,'new results directory'):
                    prep.run(prep.ROOT/'bin/never-create-this-directory')
                inputs.assert_not_called()

    def test_signed_coefficient_bound(self):
        for raw in [(32769,0),(0,-32769),(0.1,0),(0,0,0)]:
            with self.assertRaises(ValueError):prep.SupportedPawnProbe(raw)


if __name__=='__main__':unittest.main()
