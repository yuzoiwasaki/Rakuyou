#!/usr/bin/env python3
"""Dry-run execution guards, backup integrity, and synthetic-only update wiring."""
import json
import sys
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent.parent/"tools"))
from learning_backup import create_backup,verify_backup,safe_path
from prepare_learning_data import ROOT,digest
from tempo_pilot import load_plan,assert_disjoint,advance
from tempo_updater import Config,initial
from tempo_objective import FrozenLeaf


class PilotTest(unittest.TestCase):
    def test_default_plan_does_not_allow_real_updates(self):
        plan=ROOT/"docs/experiments/configs/tempo-pilot-v1.json"
        self.assertFalse(load_plan(plan)["real_data_training_enabled"])
        with self.assertRaises(ValueError):load_plan(plan,True)

    def test_untested_settings_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            data=json.loads((ROOT/"docs/experiments/configs/tempo-pilot-v1.json").read_text())
            data["optimizer"]["max_updates"]=100
            p=Path(directory)/"plan.json";p.write_text(json.dumps(data))
            with self.assertRaises(ValueError):load_plan(p)

    def test_run_root_and_leaf_overlap_rejected(self):
        train=[dict(row=dict(run="a",sfen="root-a"),frame=dict(leaf_sfen="leaf-a"))]
        val=[dict(row=dict(run="b",sfen="root-b"),frame=dict(leaf_sfen="leaf-b"))]
        assert_disjoint(train,val)
        val[0]["frame"]["leaf_sfen"]="leaf-a"
        with self.assertRaises(ValueError):assert_disjoint(train,val)

    def test_update_wiring_uses_finite_bounded_synthetic_gradient(self):
        c=Config();s=initial(c)
        samples=[FrozenLeaf(0,200,.5,"black","black")]
        changed=advance(s,samples,c)
        self.assertEqual(changed.updates,1)
        self.assertTrue(0<changed.delta[1]<=.25)
        self.assertEqual(changed.delta[0],0)
        self.assertEqual(changed.delta[2],0)

    def test_backup_separate_bytes_and_tamper_detection(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/"data").mkdir()
            source=root/"data/input.json";source.write_text("original")
            backup=root/"backup";create_backup(["data/input.json"],backup,root)
            m=backup/"manifest.json"
            verify_backup(m,{"data/input.json":digest(source)},root)
            copy=backup/"files/data/input.json"
            self.assertNotEqual(source.stat().st_ino,copy.stat().st_ino)
            copy.write_text("changed")
            self.assertEqual(source.read_text(),"original")
            with self.assertRaises(ValueError):verify_backup(m,root=root)

    def test_backup_path_escape_and_missing_requirement_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/"source").write_text("content")
            with self.assertRaises(ValueError):safe_path(root,"../escape")
            create_backup(["source"],root/"backup",root)
            with self.assertRaises(ValueError):verify_backup(root/"backup/manifest.json",{"missing":"sha"},root)
            with self.assertRaises(FileExistsError):create_backup(["source"],root/"backup",root)


if __name__=="__main__":unittest.main()
