import unittest,tempfile
from pathlib import Path
from unittest.mock import patch
from tools.learning.imitation import imitation_search_review as r

class SearchReviewTests(unittest.TestCase):
    def test_protected_bytes(self):
        layout=dict(kp_offset=0,pp_offset=16,controls_offset=32,bytes=48)
        with tempfile.TemporaryDirectory() as folder:
            a=Path(folder)/'base';b=Path(folder)/'candidate';a.write_bytes(bytes(48))
            for index in (12,20,28,32):
                data=bytearray(48);data[index]=1;b.write_bytes(data)
                with self.assertRaises(ValueError):r.audit_bytes(a,b,layout)
            data=bytearray(48);data[0]=1;data[24]=2;b.write_bytes(data)
            self.assertEqual(r.audit_bytes(a,b,layout),2)

    def test_selection_ignores_quality(self):
        rows=[{'row':dict(id=str(i),stratum='a' if i<3 else 'b'), 'score':i} for i in range(6)]
        before=[x['row']['id'] for x in r.choose(rows)]
        for row in rows:row['score']=-1000;row['feature']=1000
        self.assertEqual(before,[x['row']['id'] for x in r.choose(list(reversed(rows)))])

    def test_changed_fixed_candidate_rejected_before_output(self):
        with tempfile.TemporaryDirectory(dir=r.ROOT/'results') as folder:
            output=Path(folder)/'new'
            with patch.object(r,'digest',return_value='changed'):
                with self.assertRaisesRegex(ValueError,'Fixed20'):r.run(output)
            self.assertFalse(output.exists())

if __name__=='__main__':unittest.main()
