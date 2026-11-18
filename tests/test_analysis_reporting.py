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
    def test_convergence_diagnostics_appear_only_for_convergence_analysis(self):
        temporary_root = PROJECT_ROOT / '.autodev'
        temporary_root.mkdir(exist_ok=True)
        for mode in ('batch', 'rpm', 'convergence'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory(dir=temporary_root) as directory:
                result = {'analysis': mode, 'cases': [
                    {'name': 'base', 'ok': True, 'summary': {'seconds': 12}},
                ]}
                if mode == 'convergence':
                    result['commonTimeStepSeconds'] = 0.25
                folder = export_analysis(result, directory)
                report = (folder / 'ANALYSIS_REPORT.md').read_text(encoding='utf-8')
                self.assertIn('| base | OK | None | 12 |', report)
                if mode == 'convergence':
                    self.assertIn('## Convergence diagnostics', report)
                    self.assertIn('"commonTimeStepSeconds": 0.25', report)
                    self.assertIn('## Interpretation', report)
                else:
                    self.assertNotIn('## Convergence diagnostics', report)
                    self.assertNotIn('## Interpretation', report)
                self.assertEqual(json.loads((folder / 'analysis.json').read_text(encoding='utf-8')), result)

    def test_sensitivity_report_explains_elasticities_and_unavailable_results(self):
        result = {'analysis': 'sensitivity', 'sensitivities': [
            {'parameter': 'rpm', 'available': True, 'timeElasticity': -0.8, 'energyElasticity': 0},
            {'parameter': 'flow', 'available': False, 'reason': 'target_not_reached'},
            {'parameter': 'href', 'available': False, 'reason': 'invalid_case'},
            {'parameter': 'exchangePerRev', 'available': False, 'reason': 'zero_parameter_span'},
            {'parameter': 'other', 'available': False, 'reason': 'zero_response'},
        ]}
        temporary_root = PROJECT_ROOT / '.autodev'
        temporary_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temporary_root) as directory:
            folder = export_analysis(result, directory)
            report = (folder / 'ANALYSIS_REPORT.md').read_text(encoding='utf-8')
            self.assertIn('## Local sensitivity', report)
            self.assertIn('Elasticities are dimensionless.', report)
            self.assertIn('| rpm | -0.8 | 0 | Available |', report)
            self.assertIn('| flow | — | — | A required case did not reach the target. |', report)
            self.assertIn('| href | — | — | A required case failed. |', report)
            self.assertIn('| exchangePerRev | — | — | The baseline parameter or perturbation span is zero. |', report)
            self.assertIn('| other | — | — | The baseline target time is nonpositive or the baseline input energy is zero. |', report)
            self.assertNotIn('## Convergence diagnostics', report)
            self.assertEqual(json.loads((folder / 'analysis.json').read_text(encoding='utf-8')), result)

    def test_sizing_report_explains_the_outcome_without_convergence_diagnostics(self):
        scenarios = [
            ({'possible': True, 'kw': 12.5}, 'Conditional power: 12.5 kW.'),
            ({'possible': False, 'limitKW': 1000, 'reason': 'target not reached'},
             'Search power limit: 1000 kW.\nReason: target not reached.'),
        ]
        temporary_root = PROJECT_ROOT / '.autodev'
        temporary_root.mkdir(exist_ok=True)
        for outcome, expected in scenarios:
            with self.subTest(outcome=outcome), tempfile.TemporaryDirectory(dir=temporary_root) as directory:
                folder = export_analysis({'analysis': 'sizing', **outcome}, directory)
                report = (folder / 'ANALYSIS_REPORT.md').read_text(encoding='utf-8')
                self.assertIn('## Conditional power sizing', report)
                self.assertIn(expected, report)
                self.assertNotIn('## Measured outputs', report)
                self.assertNotIn('## Convergence diagnostics', report)
                digest = hashlib.sha256((folder / 'analysis.json').read_bytes()).hexdigest()
                self.assertIn(f'Analysis JSON SHA-256: `{digest}`.', report)

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
            self.assertIn('No local sensitivity diagnostics were returned.', report)
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
