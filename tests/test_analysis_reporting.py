"""Analysis reports must expose native failures without corrupting tables."""
import csv
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from rotary_melter.AnalysisReporting import export_analysis
from rotary_melter.Paths import PROJECT_ROOT


class AnalysisReportingTests(unittest.TestCase):
    def test_empty_analysis_replaces_previous_csv_rows(self):
        temporary_root = PROJECT_ROOT / '.autodev'
        temporary_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temporary_root) as directory:
            folder = export_analysis({'cases': [{'name': 'previous', 'ok': True}]}, directory)
            with (folder / 'analysis.csv').open(encoding='utf-8-sig', newline='') as stream:
                previous = csv.DictReader(stream)
                expected_fields = previous.fieldnames
                self.assertEqual(len(list(previous)), 1)
            result = {'analysis': 'required_power', 'cases': [], 'possible': False}
            export_analysis(result, directory)
            with (folder / 'analysis.csv').open(encoding='utf-8-sig', newline='') as stream:
                current = csv.DictReader(stream)
                self.assertEqual(current.fieldnames, expected_fields)
                self.assertEqual(list(current), [])
            manifest = json.loads((folder / 'run_manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(manifest['cases'], 0)
            self.assertEqual(json.loads((folder / 'analysis.json').read_text(encoding='utf-8')), result)

    def test_result_hash_matches_exported_file_bytes(self):
        temporary_root = PROJECT_ROOT / '.autodev'
        temporary_root.mkdir(exist_ok=True)
        result = {'analysis': 'Duyarlılık ölçümü', 'cases': [
            {'name': 'Debi değişimi', 'ok': True, 'summary': {'seconds': 12.5}},
        ]}
        with tempfile.TemporaryDirectory(dir=temporary_root) as directory:
            folder = export_analysis(result, directory)
            payload = (folder / 'analysis.json').read_bytes()
            expected_hash = hashlib.sha256(payload).hexdigest()
            manifest = json.loads((folder / 'run_manifest.json').read_text(encoding='utf-8'))
            report = (folder / 'ANALYSIS_REPORT.md').read_text(encoding='utf-8')
            self.assertEqual(json.loads(payload), result)
            self.assertEqual(manifest['resultSha256'], expected_hash)
            self.assertIn(f'Analysis JSON SHA-256: `{expected_hash}`.', report)

    def test_cancelled_cases_are_explicit_in_report_and_csv(self):
        result = {'cases': [
            {'name': 'interrupted|case', 'ok': True,
             'summary': {'cancelled': True, 'seconds': 3}},
            {'name': 'finished', 'ok': True,
             'summary': {'cancelled': False, 'targetReached': False}},
            {'name': 'failed and cancelled', 'ok': False, 'error': 'native error',
             'summary': {'cancelled': True}},
        ]}
        temporary_root = PROJECT_ROOT / '.autodev'
        temporary_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temporary_root) as directory:
            folder = export_analysis(result, directory)
            report = (folder / 'ANALYSIS_REPORT.md').read_text(encoding='utf-8')
            self.assertIn('| interrupted&#124;case | CANCELLED | None | 3 |', report)
            self.assertIn('| finished | OK | False |', report)
            self.assertIn('| failed and cancelled | FAILED |', report)
            self.assertIn('| failed and cancelled | native error |', report)
            self.assertIn('## Cancelled cases', report)
            self.assertIn('their outputs are partial results', report)
            self.assertIn('| interrupted&#124;case | CANCELLED |', report)
            with (folder / 'analysis.csv').open(encoding='utf-8-sig', newline='') as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual([row['cancelled'] for row in rows], ['True', 'False', 'True'])
            self.assertEqual(json.loads((folder / 'analysis.json').read_text(encoding='utf-8')), result)

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
