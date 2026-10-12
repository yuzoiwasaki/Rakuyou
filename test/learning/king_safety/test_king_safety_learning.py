
# Permit direct CLI execution as well as package imports.
import sys as _sys
from pathlib import Path as _RepoPath
if not __package__:
    _sys.path.insert(0, str(_RepoPath(__file__).resolve().parents[3]))
import json
import subprocess
import sys
import unittest
from pathlib import Path
from tools.learning.core.king_safety_objective import FrozenLeaf, check_gradient, objective
from tools.learning.core.king_safety_updater import Config, initial, step, checkpoint, restore
from tools.learning.core.king_safety_export import validate_map
from tools.learning.king_safety.king_safety_pilot import independent_columns, PROBE
from tools.learning.data.prepare_learning_data import ROOT


def flip_sfen(sfen,rotate=False):
    board,side,hand,ply=sfen.split();rows=[]
    for row in board.split('/'):
        cells=[];i=0
        while i<len(row):
            if row[i].isdigit():cells.extend(['.']*int(row[i]));i+=1
            elif row[i]=='+':cells.append(row[i:i+2]);i+=2
            else:cells.append(row[i]);i+=1
        rows.append(list(reversed(cells)))
    if rotate:rows=list(reversed(rows));rows=[[c.swapcase() if c!='.' else c for c in row] for row in rows]
    encoded=[]
    for row in rows:
        text='';blanks=0
        for c in row:
            if c=='.':blanks+=1
            else:
                if blanks:text+=str(blanks);blanks=0
                text+=c
        if blanks:text+=str(blanks)
        encoded.append(text)
    if rotate:side='w' if side=='b' else 'b';hand=hand.swapcase()
    return '/'.join(encoded)+' '+side+' '+hand+' '+ply


class SafetyLearningTest(unittest.TestCase):
    def test_eight_gradient_color_and_progress(self):
        samples=[FrozenLeaf(-100,200,.2,'black',(1,-1,2,0)),FrozenLeaf(50,-40,.8,'white',(-2,1,0,3))]
        check_gradient(samples,(0,)*8);check_gradient(samples,(.01,-.02)*4)
        a=samples[0];b=FrozenLeaf(a.base_root_cp,a.teacher_root_cp,a.progress,'white',a.counts)
        self.assertEqual(tuple(-x for x in a.factors()),b.factors())

    def test_bounded_twenty_and_checkpoint_identity(self):
        config=Config();state=initial(config)
        for _ in range(20):state=step(state,(.01,)*8,config)
        self.assertTrue(all(abs(x)<=.5 for x in state.delta))
        payload=json.loads(json.dumps(checkpoint(state,config,{'input':'test'})))
        self.assertEqual(restore(payload,config,{'input':'test'}),state)
        with self.assertRaises(ValueError):step(state,(.01,)*8,config)
        with self.assertRaises(ValueError):restore(payload,config,{'input':'other'})

    def test_rank_freezes_unseen_duplicate_features(self):
        samples=[FrozenLeaf(0,1,.2,'black',(1,1,0,0)),FrozenLeaf(0,1,.8,'black',(1,1,0,0))]
        self.assertEqual(independent_columns(samples),[0,1])

    def test_export_mask_rejects_outside_and_duplicates(self):
        layout=dict(bytes=259336912,scale=65536,begin=32,table_bytes=64,entries=[[32,1],[48,9]])
        validate_map(layout)
        for entries in ([[16,1]],[[32,1],[32,1]],[[32,0]],[[33,1]]):
            with self.assertRaises(ValueError):validate_map({**layout,'entries':entries})

    def test_native_feature_semantics_and_king_exclusion(self):
        cases=[
            ('k8/9/9/9/9/9/9/4G4/4K4 b - 1',[0,0,1,0]),
            ('k8/9/9/9/9/9/9/4G4/4KS3 b - 1',[1,0,1,0]),
            ('k8/9/9/9/9/9/4S4/4KG3/9 b - 1',[1,1,0,0]),
            ('k3r4/9/9/9/9/9/9/9/4K4 b - 1',[0,0,0,1]),
        ]
        proc=subprocess.run([str(PROBE),'--safety-sfen',str(ROOT/'bin/params.bin')],
            input='\n'.join(s for s,_ in cases)+'\n',text=True,capture_output=True,check=True,timeout=30)
        for (_,expected),line in zip(cases,proc.stdout.splitlines()):
            self.assertEqual(json.loads(line)['features']['black'],expected)

    def test_native_color_mirror_and_corner(self):
        gen=json.loads((ROOT/'results/learning-pilot/2026-10-11-teacher-refresh-run-v1/report.json').read_bytes())
        sfens=[x['sfen'] for x in gen['records'][:12]]
        sfens.append('8k/9/9/9/9/9/9/9/K8 b - 1')
        inputs=[x for s in sfens for x in (s,flip_sfen(s),flip_sfen(s,True))]
        proc=subprocess.run([str(PROBE),'--safety-sfen',str(ROOT/'bin/params.bin')],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True,timeout=30)
        features=[json.loads(line)['features'] for line in proc.stdout.splitlines()]
        for i in range(0,len(features),3):
            a,b,c=features[i:i+3];self.assertEqual(a,b)
            self.assertEqual(a['black'],c['white']);self.assertEqual(a['white'],c['black'])
        self.assertEqual(features[-3],{'black':[0]*4,'white':[0]*4})


if __name__=='__main__':unittest.main()
