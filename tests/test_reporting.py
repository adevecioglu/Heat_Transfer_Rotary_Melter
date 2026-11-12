"""Single-run artifacts must distinguish interrupted and completed calculations."""
import hashlib
import csv
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from rotary_melter.Paths import PROJECT_ROOT
from rotary_melter.Reporting import export_result


class ReportingStatusTests(unittest.TestCase):
    def test_equation_attachment_matches_engine(self):
        temporary_root = PROJECT_ROOT / '.autodev'
        temporary_root.mkdir(exist_ok=True)
        for native in (False, True):
            with self.subTest(native=native), \
                    tempfile.TemporaryDirectory(dir=temporary_root) as directory:
                root = Path(directory)
                catalogue_name = ('CPP_CALCULATION_EQUATIONS.md' if native
                                  else 'CALCULATION_EQUATIONS.md')
                catalogue = root / catalogue_name
                content = '# Selected equations\n\nTürkçe — °C\n'
                catalogue.write_text(content, encoding='utf-8')
                sources = root / 'native_sources'
                sources.mkdir()
                (sources / 'example.cpp').write_text('// source', encoding='utf-8')
                result = {'engine': {'name': 'Rotary Melter C++'}} if native else {}
                with patch('rotary_melter.Paths.resource_path', return_value=catalogue) as resource, \
                        patch('rotary_melter.Paths.PROJECT_ROOT', root), \
                        patch('sys.frozen', True, create=True):
                    # Frozen mode also checks the packaged-resource lookup.
                    resource.side_effect = lambda name: sources if name == 'native_sources' else root / Path(name).name
                    folder = export_result(result, root / 'run')
                self.assertEqual((folder / 'EQUATIONS.md').read_text(encoding='utf-8'), content)
                self.assertEqual((folder / 'source/native/example.cpp').exists(), native)
                self.assertIn(unittest.mock.call('docs/' + catalogue_name), resource.call_args_list)

    def test_method_description_matches_engine(self):
        temporary_root = PROJECT_ROOT / '.autodev'
        temporary_root.mkdir(exist_ok=True)
        for native in (False, True):
            with self.subTest(native=native), \
                    tempfile.TemporaryDirectory(dir=temporary_root) as directory:
                result = {'engine': {'name': 'Rotary Melter C++', 'integrator': 'rk4'}} if native else {}
                with patch('rotary_melter.Paths.resource_path',
                           return_value=Path(directory) / 'absent_catalogue.md'):
                    folder = export_result(result, directory)
                report = (folder / 'RUN_REPORT.md').read_text(encoding='utf-8')
                self.assertEqual('with Eigen' in report, native)
                self.assertEqual('Boost.Odeint' in report, native)
                self.assertEqual('V11 JavaScript reference time-stepping' in report, not native)
                engine_name = 'Rotary Melter C++' if native else 'V11 JavaScript reference'
                self.assertIn(f'- Engine: `{engine_name}`', report)
                self.assertEqual(json.loads((folder / 'result.json').read_text(encoding='utf-8')), result)

    def test_history_link_requires_exported_samples(self):
        temporary_root = PROJECT_ROOT / '.autodev'
        temporary_root.mkdir(exist_ok=True)
        samples = [{'t': 0, 'coreC': 25}, {'t': 1, 'coreC': 26}]
        for history in (None, [], samples):
            with self.subTest(history=history), \
                    tempfile.TemporaryDirectory(dir=temporary_root) as directory:
                result = {} if history is None else {'hist': history}
                with patch('rotary_melter.Paths.resource_path',
                           return_value=Path(directory) / 'absent_catalogue.md'):
                    folder = export_result(result, directory)
                report = (folder / 'report.html').read_text(encoding='utf-8')
                self.assertIn('href="result.json"', report)
                self.assertEqual('href="history.csv"' in report, bool(history))
                self.assertEqual('No time-series samples' in report, not bool(history))
                self.assertEqual((folder / 'history.csv').exists(), bool(history))
                if history:
                    with (folder / 'history.csv').open(encoding='utf-8-sig', newline='') as stream:
                        self.assertEqual(list(csv.DictReader(stream)),
                                         [{'t': '0', 'coreC': '25'}, {'t': '1', 'coreC': '26'}])

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
                    html_report = (folder / 'report.html').read_text(encoding='utf-8')
                    self.assertIn(f'Status: <strong>{status}</strong>.', html_report)
                    self.assertEqual('outputs are partial results' in html_report, bool(cancelled))
                    self.assertIn(f'| Target reached | {reached} |', report)
                    manifest = json.loads((folder / 'run_manifest.json').read_text(encoding='utf-8'))
                    self.assertIs(manifest['cancelled'], bool(cancelled))
                    payload = (folder / 'result.json').read_bytes()
                    self.assertEqual(json.loads(payload), result)
                    self.assertEqual(manifest['resultSha256'], hashlib.sha256(payload).hexdigest())
