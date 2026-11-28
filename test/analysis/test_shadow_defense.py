"""Do not confuse rule-driven switches with changed search results."""
import unittest
from tools.analysis.shadow_defense_game import summarize_case


def cp(move,score,depth=18):return dict(pv=[move],score=str(score),depth=depth,score_type='cp')


class ShadowDefenseTest(unittest.TestCase):
    def test_distinguish_switch_research_and_no_change(self):
        self.assertEqual(summarize_case('8e8f',[cp('8e8f',-100),cp('P*6d',-150)],['P*6d'])['kind'],'within50-switch')
        self.assertEqual(summarize_case('8e8f',[cp('8e8f',-100),cp('P*6d',-151)],['P*6d'])['kind'],'keep-actual')
        self.assertEqual(summarize_case('8e8f',[cp('8e8f',-100),cp('P*6d',-90)],['P*6d'])['kind'],'research-already-prefers-defense')

    def test_incomplete_or_mate_not_claimed(self):
        self.assertEqual(summarize_case('8e8f',[cp('8e8f',-100,17),cp('P*6d',-110,17)],['P*6d'])['kind'],'incomplete-depth')
        mate=cp('8e8f',3);mate['score_type']='mate'
        self.assertEqual(summarize_case('8e8f',[mate,cp('P*6d',-110)],['P*6d'])['kind'],'incomparable-scores')


if __name__=='__main__':unittest.main()
