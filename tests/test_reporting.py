"""Single-run artifacts must distinguish interrupted and completed calculations."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from rotary_melter.Paths import PROJECT_ROOT
from rotary_melter.Reporting import export_result


class ReportingStatusTests(unittest.TestCase):
    def test_cancellation_is_visible_without_changing_result_payload(self):
        temporary_root = PROJECT_ROOT / '.autodev'
        temporary_root.mkdir(exist_ok=True)
        for cancelled in (True, False, None):
            for reached in (True, False):
                with self.subTest(cancelled=cancelled, reached=reached), \
                        tempfile.TemporaryDirectory(dir=temporary_root) as directory:
                    result = {'targetReached': reached, 'seconds': 12.5}
                    if cancelled is not None:
                        result['cancelled'] = cancelled
                    # Formula copying is independent of execution-status reporting.
                    with patch('rotary_melter.Paths.resource_path',
                               return_value=Path(directory) / 'absent_catalogue.md'):
                        folder = export_result(result, directory)
                    report = (folder / 'RUN_REPORT.md').read_text(encoding='utf-8')
                    status = 'CANCELLED' if cancelled else 'COMPLETED'
                    self.assertIn(f'Status: **{status}**.', report)
                    self.assertEqual('outputs are partial results' in report, bool(cancelled))
                    self.assertIn(f'| Target reached | {reached} |', report)
                    manifest = json.loads((folder / 'run_manifest.json').read_text(encoding='utf-8'))
                    self.assertIs(manifest['cancelled'], bool(cancelled))
                    payload = (folder / 'result.json').read_bytes()
                    self.assertEqual(json.loads(payload), result)
                    self.assertEqual(manifest['resultSha256'], hashlib.sha256(payload).hexdigest())
