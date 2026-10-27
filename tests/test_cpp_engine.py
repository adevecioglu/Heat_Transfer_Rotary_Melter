"""Physical regression, deterministic parallelism and native-interface checks."""
import math
import tempfile
import time
import unittest
from pathlib import Path

from rotary_melter.Configuration import load_inputs
from rotary_melter.NativeEngine import execute, info, simulate, NativeJobs
from rotary_melter.Paths import OUTPUTS_DIR


class NativeCalculationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        backend = info()
        if not backend['available']:
            raise unittest.SkipTest('Build the native engine for C++ checks: '+backend['error'])

    def scenario(self, **changes):
        data = load_inputs()
        data['inputs'].update(axialZones=4, angularZones=8, radialZones=8, maxHours=.002)
        data['inputs'].update(changes)
        return data

    def test_cold_water_initial_energy_balance(self):
        result = simulate(self.scenario())
        first = result['hist'][0]
        self.assertEqual(first['waterOut'], 25)
        self.assertEqual(first['waterIn'], 110)
        self.assertAlmostEqual(first['waterMetalKW'], 0, places=10)
        self.assertGreater(first['waterStorageKW'], 0)
        self.assertLess(abs(first['waterBalanceResidualW']), 1e-7)
        self.assertLess(result['balanceRelative'], 1e-10)

    def test_geometry_without_heads_and_vertical_fill(self):
        data = self.scenario(heads=0, headDepth=0, angle=90)
        result = execute({'action': 'geometry', 'configuration': data})
        expected = math.pi * .3**2 * .8
        self.assertAlmostEqual(result['volume'], expected, places=13)
        self.assertAlmostEqual(result['bulkFill'], .5, places=13)
        self.assertTrue(math.isfinite(result['fillProfile']['plane']))

    def test_invalid_numeric_and_correlation_inputs(self):
        for changes in ({'flow': -1}, {'radialZones': 2.5}, {'tin': 373.99}, {'returnInner': 50}):
            with self.subTest(changes=changes):
                with self.assertRaises(RuntimeError):
                    simulate(self.scenario(**changes))

    def test_if97_properties_and_conserved_reference_mode(self):
        properties = execute({'action': 'water_properties', 'temperatureC': 110, 'pressureBarAbs': 4})
        self.assertAlmostEqual(properties['saturationPressureBar'], 1.4338, delta=.002)
        self.assertTrue(940 < properties['densityKgM3'] < 960)
        self.assertTrue(4100 < properties['specificHeatJKgK'] < 4300)
        result = simulate(self.scenario(), options={'waterModel': 'if97_reference'})
        self.assertLess(result['balanceRelative'], 1e-10)
        self.assertEqual(result['engine']['waterModel'], 'if97_reference')
        self.assertIsNotNone(result['engine']['propertyReference'])

    def test_library_integrators_preserve_energy(self):
        for integrator in ('midpoint', 'rk4', 'dopri5'):
            with self.subTest(integrator=integrator):
                result = simulate(self.scenario(), options={'integrator': integrator})
                self.assertLess(result['balanceRelative'], 1e-9)
                self.assertTrue(all(24.999 <= value <= 110.001 for value in result['last']['waterZones']))

    def test_independent_case_parallel_results_are_deterministic(self):
        cases = [{'name': str(rpm), 'configuration': self.scenario(rpm=rpm)} for rpm in (0, 10, 20)]
        request = {'action': 'analyse', 'analysis': 'batch', 'configuration': self.scenario(), 'cases': cases}
        serial = execute({**request, 'options': {'threads': 1}})
        parallel = execute({**request, 'options': {'threads': 3}})
        self.assertEqual([case['name'] for case in serial['cases']], [case['name'] for case in parallel['cases']])
        for before, after in zip(serial['cases'], parallel['cases']):
            self.assertTrue(before['ok'] and after['ok'])
            for key in ('seconds', 'coreC', 'energyInKWh', 'lossKWh', 'balanceRelative'):
                self.assertEqual(before['summary'][key], after['summary'][key], key)

    def test_parallel_surface_kernel_preserves_the_solution(self):
        data = load_inputs()
        data['inputs'].update(axialZones=64, angularZones=64, radialZones=8, maxHours=.00002)
        serial = simulate(data, no_history=True, options={'threads': 1})
        parallel = simulate(data, no_history=True, options={'threads': 4, 'parallelKernel': True})
        self.assertTrue(parallel['engine']['parallelKernelActive'])
        for key in ('seconds', 'energyInKWh', 'lossKWh', 'balanceRelative'):
            self.assertEqual(serial[key], parallel[key], key)
        self.assertEqual(serial['last']['innerSurface'], parallel['last']['innerSurface'])

    def test_cancelled_calculation_is_never_reported_as_a_completed_target(self):
        result = simulate(self.scenario(), cancelled=lambda: True)
        self.assertTrue(result['cancelled'])
        self.assertEqual(result['termination'], 'cancelled')
        self.assertFalse(result['targetReached'])
        self.assertEqual(result['steps'], 0)

    def test_unreached_targets_do_not_receive_false_convergence_percentages(self):
        result = execute({'action': 'analyse', 'analysis': 'convergence', 'configuration': self.scenario(),
                          'options': {'threads': 3}})
        self.assertFalse(result['targetGci']['available'])
        self.assertEqual(result['targetGci']['reason'], 'target_not_reached')
        self.assertIsNone(result['timeDifferencePercent'])
        self.assertIsNone(result['radialDifferencePercent'])

    def test_sensitivity_keeps_valid_cases_when_one_perturbation_is_invalid(self):
        result = execute({'action': 'analyse', 'analysis': 'sensitivity',
                          'configuration': self.scenario(href=300, hLimit=300), 'options': {'threads': 3}})
        by_name = {row['name']: row for row in result['cases']}
        self.assertTrue(by_name['base']['ok'])
        self.assertFalse(by_name['href_high']['ok'])
        self.assertIn('coefficients', by_name['href_high']['error'])
        diagnostic = next(row for row in result['sensitivities'] if row['parameter'] == 'href')
        self.assertFalse(diagnostic['available'])
        self.assertEqual(diagnostic['reason'], 'invalid_case')

    def test_history_roundtrip_and_path_validation(self):
        with tempfile.TemporaryDirectory(dir=OUTPUTS_DIR) as directory:
            jobs = NativeJobs(directory)
            original = self.scenario()
            ident = jobs.start('solve', original, {'integrator': 'rk4'})['id']
            original['inputs']['flow'] = -999
            deadline = time.monotonic()+5
            while time.monotonic() < deadline:
                status = jobs.poll(ident)
                if status['status'] != 'running':
                    break
                time.sleep(.01)
            self.assertEqual(status['status'], 'complete', status)
            records = jobs.history()['runs']
            self.assertEqual(records[0]['runId'], ident)
            replay = jobs.read_result(ident)['result']
            self.assertGreater(replay['traceability']['requestedConfiguration']['inputs']['flow'], 0)
            self.assertEqual(replay['engine']['integrator'], 'rk4')
            self.assertTrue((Path(directory)/ident/'RUN_REPORT.md').exists())
            with self.assertRaises(ValueError):
                jobs.read_result('../default_inputs')

    def test_native_job_cancellation_and_isolated_artifacts(self):
        OUTPUTS_DIR.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=OUTPUTS_DIR) as directory:
            jobs = NativeJobs(directory)
            ident = jobs.start('solve', self.scenario(maxHours=1000))['id']
            jobs.cancel(ident)
            deadline = time.monotonic()+5
            while time.monotonic() < deadline:
                status = jobs.poll(ident)
                if status['status'] != 'running':
                    break
                time.sleep(.01)
            self.assertEqual(status['status'], 'cancelled')
            self.assertTrue(any(Path(directory).rglob('result.json')))


if __name__ == '__main__':
    unittest.main(verbosity=2)
