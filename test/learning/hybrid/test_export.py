"""Export orchestration tests using synthetic files and mocked native tools."""
import contextlib
import copy
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from tools.learning.hybrid import export as exporter
from tools.learning.hybrid.runner import seal, unseal


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.output = self.root/'results/experiment'
        self.arm = self.output/'mixed'
        self.arm.mkdir(parents=True)
        for name, body in [('runtime/bin/params.bin', b'baseline'),
                           ('runtime/bin/release', b'fake-engine'),
                           ('runtime/bin/progress.bin', b'progress'),
                           ('runtime/lib/libomp.dylib', b'library'),
                           ('plan.json', b'{}'), ('teachers.json', b'{}'),
                           ('mixed/delta.txt', b'0 1 2 0 0\n')]:
            path = self.output/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
        self.binary = self.root/'export-tools/export'
        self.binary.parent.mkdir()
        self.binary.write_bytes(b'fake-exporter')
        generated = self.binary.parent/'export.cc'
        generated.write_bytes(b'generated-source')
        probe = self.root/'tools/learning/native/imitation_probe.cc'
        probe.parent.mkdir(parents=True)
        probe.write_bytes(b'probe-source')
        (self.binary.parent/'build.json').write_text(json.dumps(dict(
            binary_sha256=exporter.digest(self.binary),
            generated_sha256=exporter.digest(generated),
            probe_source_sha256=exporter.digest(probe))))
        frame = dict(sfen='synthetic b - 1', eval_on=10, progress=.5, features=[],
                     on_parts=dict(kp=[0]*4, others=[0]*4),
                     off_parts=dict(kp=[0]*4, others=[0]*4))
        self.dataset = dict(rows=[dict(id='root', base_cp=10, factors={}, side='black', features=frame)])
        self.plan = dict(runtime_sha256={str(p.relative_to(self.output)): exporter.digest(p)
                        for p in (self.output/'runtime').rglob('*') if p.is_file()})
        binding = dict(plan_sha256=exporter.digest(self.output/'plan.json'),
                       teachers_sha256=exporter.digest(self.output/'teachers.json'), arm='mixed')
        seal(self.arm/'checkpoint.json', dict(stopped=True, binding=binding))
        self.report = dict(eligible_for_search=True, binding=binding,
                           checkpoint_sha256=exporter.digest(self.arm/'checkpoint.json'),
                           evaluation=dict(sidecar_sha256=exporter.digest(self.arm/'delta.txt'),
                                           observations=[dict(id='root', candidate_cp=10)]))
        seal(self.arm/'report.json', self.report)

    def mocks(self, *, zero_matches=True):
        stack = contextlib.ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(patch.object(exporter, 'ROOT', self.root))
        stack.enter_context(patch.object(exporter, 'EXPORTER', self.binary))
        self.load = stack.enter_context(patch.object(exporter, 'load_dataset', return_value=(self.plan, self.dataset)))

        def candidate(command, **kwargs):
            Path(command[3]).write_bytes(b'candidate')
            return json.dumps(dict(layout='synthetic'))

        def zero(command, **kwargs):
            Path(command[3]).write_bytes(b'baseline' if zero_matches else b'wrong-zero')

        def copy_file(source, target, sha):
            self.assertEqual(exporter.digest(source), sha)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)

        self.candidate = stack.enter_context(patch.object(exporter.subprocess, 'check_output', side_effect=candidate))
        self.zero = stack.enter_context(patch.object(exporter.subprocess, 'run', side_effect=zero))
        self.audit = stack.enter_context(patch.object(exporter, 'audit_bytes', return_value=3))
        self.native = stack.enter_context(patch.object(exporter, 'native_frames', return_value=[copy.deepcopy(self.dataset['rows'][0]['features'])]))
        self.copier = stack.enter_context(patch.object(exporter, 'copy_verified', side_effect=copy_file))
        stack.enter_context(contextlib.redirect_stdout(io.StringIO()))

    def test_fixed_final_candidate_creates_isolated_runtime_and_audit(self):
        self.mocks()
        result = exporter.export(self.output, 'mixed')
        runtime = self.arm/'runtime'
        self.assertEqual((runtime/'bin/params.bin').read_bytes(), b'candidate')
        self.assertEqual((runtime/'bin/release').read_bytes(), b'fake-engine')
        self.assertEqual((self.output/'runtime/bin/params.bin').read_bytes(), b'baseline')
        self.assertEqual(result['static_checks'], 1)
        self.assertEqual(result['searches'], 0)
        self.assertFalse(result['deployed'])
        self.assertEqual(result['changed_bytes'], 3)
        self.assertEqual(unseal(self.arm/'export-audit.json'), result)
        self.audit.assert_called_once_with(self.output/'runtime/bin/params.bin', runtime/'bin/params.bin', dict(layout='synthetic'))
        self.assertEqual(self.copier.call_count, 3)
        self.native.assert_called_once_with(self.plan, self.output, self.dataset['rows'], params=runtime/'bin/params.bin')
        self.assertEqual(self.load.call_count, 3)

    def test_zero_export_mismatch_rejects(self):
        self.mocks(zero_matches=False)
        with self.assertRaisesRegex(ValueError, 'Zero export'):
            exporter.export(self.output, 'mixed')
        self.audit.assert_not_called()
        self.native.assert_not_called()
        self.assertFalse((self.arm/'export-audit.json').exists())

    def test_existing_protected_byte_audit_failure_propagates(self):
        self.mocks()
        self.audit.side_effect = ValueError('Protected evaluation bytes changed')
        with self.assertRaisesRegex(ValueError, 'Protected evaluation bytes'):
            exporter.export(self.output, 'mixed')
        self.copier.assert_not_called()
        self.native.assert_not_called()
        self.assertFalse((self.arm/'export-audit.json').exists())

    def test_changed_sidecar_rejected_before_export(self):
        self.mocks()
        (self.arm/'delta.txt').write_text('0 1 2 0 1\n')
        with self.assertRaisesRegex(ValueError, 'eligible final arm'):
            exporter.export(self.output, 'mixed')
        self.candidate.assert_not_called()
        self.assertFalse((self.arm/'runtime').exists())

    def test_ineligible_report_rejected_before_export(self):
        self.mocks()
        self.report['eligible_for_search'] = False
        seal(self.arm/'report.json', self.report)
        with self.assertRaisesRegex(ValueError, 'eligible final arm'):
            exporter.export(self.output, 'mixed')
        self.candidate.assert_not_called()
        self.assertFalse((self.arm/'runtime').exists())
