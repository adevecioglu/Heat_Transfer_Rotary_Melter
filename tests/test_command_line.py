"""Headless analysis exit status must reflect failed or cancelled cases."""
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from rotary_melter.CommandLine import main
from rotary_melter.Paths import PROJECT_ROOT


class AnalysisExitStatusTests(unittest.TestCase):
    def test_analysis_status_preserves_diagnostic_exports(self):
        scenarios = [
            ([{'name': 'failed', 'ok': False, 'error': 'invalid flow'},
              {'name': 'valid', 'ok': True}], 1),
            ([{'name': 'cancelled', 'ok': True, 'summary': {'cancelled': True}}], 1),
            ([{'name': 'target missed', 'ok': True,
               'summary': {'targetReached': False, 'cancelled': False}}], 0),
            ([{'name': 'reached', 'ok': True, 'summary': {'targetReached': True}}], 0),
            ([], 0),  # Sizing analyses do not return independent cases.
        ]
        temporary_root = PROJECT_ROOT / '.autodev'
        temporary_root.mkdir(exist_ok=True)
        for cases, expected in scenarios:
            with self.subTest(cases=cases), tempfile.TemporaryDirectory(dir=temporary_root) as directory:
                result = {'analysis': 'sensitivity', 'cases': cases}
                stdout, stderr = io.StringIO(), io.StringIO()
                with patch('rotary_melter.NativeEngine.execute', return_value=result), \
                        redirect_stdout(stdout), redirect_stderr(stderr):
                    status = main(['--analyse', 'sensitivity', '--output', directory])
                self.assertEqual(status, expected)
                folder = Path(directory)
                self.assertEqual(json.loads((folder / 'analysis.json').read_text(encoding='utf-8')), result)
                for name in ('run_manifest.json', 'ANALYSIS_REPORT.md'):
                    self.assertTrue((folder / name).is_file())
                if cases:
                    self.assertTrue((folder / 'analysis.csv').is_file())
                self.assertIn(str(folder.resolve()), stdout.getvalue())
                self.assertEqual('Failed or cancelled analysis cases: 1' in stderr.getvalue(), bool(expected))
