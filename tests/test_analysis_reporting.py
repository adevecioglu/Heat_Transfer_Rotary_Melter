"""Analysis reports must expose native failures without corrupting tables."""
import csv
import json
from pathlib import Path
import tempfile
import unittest

from rotary_melter.AnalysisReporting import export_analysis
from rotary_melter.Paths import PROJECT_ROOT


class AnalysisReportingTests(unittest.TestCase):
    def test_mixed_cases_preserve_errors_and_distinguish_target_miss(self):
        result = {'analysis': 'sensitivity', 'cases': [
            {'name': 'valid', 'ok': True, 'summary': {'targetReached': False, 'seconds': 12}},
            {'name': 'bad|case', 'ok': False, 'error': 'invalid <input>\r\nflow | value'},
            {'name': 'missing detail', 'ok': False},
        ]}
        temporary_root = PROJECT_ROOT / '.autodev'
        temporary_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temporary_root) as directory:
            folder = export_analysis(result, directory)
            report = (folder / 'ANALYSIS_REPORT.md').read_text(encoding='utf-8')
            self.assertIn('| valid | OK | False | 12 |', report)
            self.assertIn('| bad&#124;case | FAILED |', report)
            self.assertIn('| bad&#124;case | invalid &lt;input&gt;<br>flow &#124; value |', report)
            self.assertIn('| missing detail | No error detail provided. |', report)
            self.assertEqual(json.loads((folder / 'analysis.json').read_text(encoding='utf-8')), result)
            with (folder / 'analysis.csv').open(encoding='utf-8-sig', newline='') as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(rows[1]['error'], result['cases'][1]['error'])

    def test_successful_cases_have_no_failure_section(self):
        temporary_root = PROJECT_ROOT / '.autodev'
        temporary_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temporary_root) as directory:
            folder = export_analysis({'cases': [{'name': 'valid', 'ok': True}]}, directory)
            report = (folder / 'ANALYSIS_REPORT.md').read_text(encoding='utf-8')
            self.assertNotIn('## Failed cases', report)
