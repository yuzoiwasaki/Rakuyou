"""Checks for the offline move-role prototype, not proof of strategic intent."""
import json
from pathlib import Path
import unittest
from tools.analysis.defense_move_audit import classify_lines
from tools.analysis.defense_preference_audit import select
from test.analysis.test_legal_entry import flip_move, flip_sfen
ROOT=Path(__file__).resolve().parents[2]


class DefenseMoveTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (ROOT/'results/defense-move-tools/native-test').exists() or not (ROOT/'bin/params.bin').exists():
            raise unittest.SkipTest('make defense-move-test and install evaluation data first')
        cls.fixtures=json.loads((ROOT/'test/analysis/defense_move_positions.json').read_text())
        cls.rows=classify_lines(['moves '+' '.join(f['moves']) for f in cls.fixtures])
        cls.by_id={f['id']:r for f,r in zip(cls.fixtures,cls.rows)}

    def test_known_defense_attack_and_wait(self):
        r=self.by_id['defense50']
        self.assertEqual(r['P*6d']['role'],'defense')
        self.assertTrue(r['P*6d']['blockade'])
        self.assertEqual(r['5b4c']['role'],'defense')
        self.assertEqual(r['5b4c']['links'],['5d'])
        self.assertEqual(r['8e8f']['role'],'attack')
        self.assertEqual(r['8e8f']['threats'],['8g'])
        self.assertEqual(r['6b7a']['role'],'unknown')
        self.assertEqual(r['2a3c']['role'],'unknown')
        self.assertEqual(r['6c6d']['links'],[])  # Pinned silver does not add support.

    def test_capture_check_and_ambiguous_moves_are_protected(self):
        self.assertEqual(self.by_id['recapture38']['3b2b']['role'],'tactical')
        evasion=self.by_id['check-after57']
        self.assertTrue(evasion)
        self.assertEqual({r['role'] for r in evasion.values()},{'evasion'})
        self.assertEqual(self.by_id['attack48-older']['5b4c']['role'],'unknown')
        self.assertTrue(any(v['role']=='mixed' for r in self.rows for v in r.values()))

    def test_supported_but_losing_blocker_is_not_defense(self):
        r=self.by_id['edge-attack52']['5c4d']
        self.assertTrue(r['exposed'])
        self.assertNotEqual(r['role'],'defense')
        # Offering an attacking pawn must not turn its role into "unknown".
        r=self.by_id['defense50']['8e8f']
        self.assertTrue(r['exposed'])
        self.assertEqual(r['role'],'attack')

    def test_replay_and_color_symmetry(self):
        sfens=[f['sfen'] for f in self.fixtures]
        saved=classify_lines(['sfen '+s for s in sfens])
        self.assertEqual(saved,self.rows)
        flipped=classify_lines(['sfen '+flip_sfen(s) for s in sfens])
        def square(s): return flip_move('P*'+s)[2:]
        for orig,other in zip(saved,flipped):
            expected={flip_move(m):dict(role=v['role'],blockade=v['blockade'],exposed=v['exposed'],
                       links=sorted(square(s) for s in v['links']),
                       threats=sorted(square(s) for s in v['threats'])) for m,v in orig.items()}
            normalized={m:dict(v,links=sorted(v['links']),threats=sorted(v['threats'])) for m,v in other.items()}
            self.assertEqual(expected,normalized)

    def test_auto_roles_feed_fifty_point_selector(self):
        r=self.by_id['defense50']
        defense=[m for m,v in r.items() if v['role']=='defense']
        attack=[m for m,v in r.items() if v['role']=='attack']
        # Synthetic scores verify wiring only; these are not search results.
        c=lambda m,s:dict(pv=[m],score=str(s),score_type='cp',depth=18)
        self.assertEqual(select([c('8e8f',0),c('5b4c',-50)],defense,attack)['selected'],'5b4c')
        self.assertEqual(select([c('8e8f',0),c('5b4c',-51)],defense,attack)['selected'],'8e8f')


if __name__=='__main__': unittest.main()
