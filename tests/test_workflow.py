"""Integration checks for the reorganized V11 source and local entry points."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from rotary_melter.Configuration import load_inputs, save_inputs
from rotary_melter.Paths import DEFAULT_CONFIG, OUTPUTS_DIR, PROJECT_ROOT


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        OUTPUTS_DIR.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='workflow_', dir=OUTPUTS_DIR)
        self.addCleanup(self.temporary.cleanup)
        self.work = Path(self.temporary.name)

    def app(self, *arguments):
        result = subprocess.run([sys.executable, str(PROJECT_ROOT / 'app.py'), *map(str, arguments)],
                                cwd=self.work, env=dict(os.environ, PYTHONUTF8='1'),
                                capture_output=True, text=True, encoding='utf-8', timeout=120)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def test_default_scenario_found_from_another_directory(self):
        self.app('--write-default', 'scenario.json')
        self.assertEqual(load_inputs(self.work / 'scenario.json'), load_inputs(DEFAULT_CONFIG))

    def test_headless_calculation_exports_conserved_result(self):
        data = load_inputs()
        data['inputs'].update(initial=74, target=75, waterInitial=75, metalInitial=75,
                              axialZones=4, angularZones=8, maxHours=.01)
        save_inputs(data, self.work / 'scenario.json')
        self.app('--run', '--config', 'scenario.json', '--output', 'result')
        for name in ('result.json', 'history.csv', 'summary.json', 'report.html'):
            self.assertGreater((self.work / 'result' / name).stat().st_size, 0)
        result = json.loads((self.work / 'result' / 'result.json').read_text(encoding='utf-8'))
        self.assertLess(result['balanceRelative'], 1e-9)
        self.assertGreater(len(result['hist']), 1)

    def test_invalid_json_values_rejected(self):
        target = self.work / 'invalid.json'
        target.write_text('{"inputs":{"flow":NaN}}', encoding='utf-8')
        with self.assertRaises(ValueError):
            load_inputs(target)

    def test_workspace_integrity_and_revision_conflicts(self):
        from tests.workspace_checks import run
        result = run()
        for check in result['checks']:
            with self.subTest(check=check['name']):
                self.assertTrue(check['passed'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
