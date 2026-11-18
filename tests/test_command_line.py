"""Headless commands must reject conflicting actions and report analysis failures."""
from argparse import ArgumentParser
from contextlib import redirect_stderr, redirect_stdout
import io
from itertools import combinations
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from rotary_melter.CommandLine import main
from rotary_melter.Paths import PROJECT_ROOT


class CalculationActionTests(unittest.TestCase):
    def test_other_action_pairs_fail_before_dispatch(self):
        parse_args = ArgumentParser.parse_args

        def parse_then_stop(parser, arguments):
            parse_args(parser, arguments)
            self.fail('Argument parser accepted two primary actions')

        actions = (
            ['--build'], ['--run'], ['--analyse', 'rpm'], ['--write-default', 'unused.json'],
            ['--self-test', 'unused.json'], ['--gpu-info', 'unused.json'],
        )
        for first, second in combinations(actions, 2):
            if (first[0], second[0]) == ('--run', '--analyse'):
                continue  # Covered for every analysis mode below.
            with self.subTest(first=first[0], second=second[0]):
                stderr = io.StringIO()
                with patch.object(ArgumentParser, 'parse_args', parse_then_stop), \
                        redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
                    main(first + second)
                self.assertEqual(raised.exception.code, 2)
                self.assertIn(first[0], stderr.getvalue())
                self.assertIn(second[0], stderr.getvalue())

    def test_run_and_analysis_conflict_before_loading_or_exporting(self):
        for analysis in ('convergence', 'sensitivity', 'rpm', 'sizing'):
            for arguments in (['--run', '--analyse', analysis],
                              ['--analyse', analysis, '--run']):
                with self.subTest(arguments=arguments):
                    stderr = io.StringIO()
                    with patch('rotary_melter.CommandLine.load_inputs') as load, \
                            patch('rotary_melter.NativeEngine.execute') as execute, \
                            patch('rotary_melter.Reporting.export_result') as export, \
                            patch('rotary_melter.AnalysisReporting.export_analysis') as export_analysis, \
                            redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
                        main(arguments)
                    self.assertEqual(raised.exception.code, 2)
                    self.assertIn('not allowed with argument', stderr.getvalue())
                    self.assertIn('--run', stderr.getvalue())
                    self.assertIn('--analyse', stderr.getvalue())
                    for operation in (load, execute, export, export_analysis):
                        operation.assert_not_called()


class EngineOptionTests(unittest.TestCase):
    def test_javascript_rejects_cpp_options_before_loading_inputs(self):
        destination = PROJECT_ROOT / '.autodev' / 'javascript_options_report'
        for option, value in (('--integrator', 'midpoint'), ('--threads', '2'),
                              ('--water-model', 'if97_reference')):
            with self.subTest(option=option):
                stderr = io.StringIO()
                with patch('rotary_melter.CommandLine.load_inputs') as load, \
                        patch('rotary_melter.JavaScriptEngine.simulate') as simulate, \
                        patch('rotary_melter.Reporting.export_result', return_value=destination) as export, \
                        redirect_stderr(stderr), redirect_stdout(io.StringIO()):
                    with self.assertRaises(SystemExit) as raised:
                        main(['--run', '--engine', 'javascript', option, value])
                self.assertEqual(raised.exception.code, 2)
                self.assertIn(f'{option} requires --engine cpp', stderr.getvalue())
                load.assert_not_called()
                simulate.assert_not_called()
                export.assert_not_called()

    def test_cpp_run_keeps_default_and_explicit_options(self):
        destination = PROJECT_ROOT / '.autodev' / 'cpp_options_report'
        for arguments, expected in (
            ([], {'integrator': 'midpoint', 'threads': 4, 'waterModel': 'constant'}),
            (['--integrator', 'rk4', '--threads', '2', '--water-model', 'if97_reference'],
             {'integrator': 'rk4', 'threads': 2, 'waterModel': 'if97_reference'}),
        ):
            with self.subTest(arguments=arguments):
                configuration = {}
                with patch('rotary_melter.CommandLine.load_inputs', return_value=configuration), \
                        patch('rotary_melter.NativeEngine.simulate', return_value={}) as simulate, \
                        patch('rotary_melter.Reporting.export_result', return_value=destination), \
                        redirect_stdout(io.StringIO()):
                    self.assertEqual(main(['--run', *arguments]), 0)
                simulate.assert_called_once_with(configuration, options={**expected, 'parallelKernel': True})


class CalculationExitStatusTests(unittest.TestCase):
    def test_cancelled_run_exports_before_returning_failure(self):
        for engine in ('cpp', 'javascript'):
            for cancelled, reached, expected in ((True, False, 1), (False, False, 0),
                                                  (False, True, 0), (None, False, 0)):
                with self.subTest(engine=engine, cancelled=cancelled, reached=reached):
                    result = {'targetReached': reached, 'seconds': 12.5}
                    if cancelled is not None:
                        result['cancelled'] = cancelled
                    stdout, stderr = io.StringIO(), io.StringIO()
                    destination = PROJECT_ROOT / '.autodev' / 'cancelled_run_report'
                    module = 'NativeEngine' if engine == 'cpp' else 'JavaScriptEngine'
                    with patch(f'rotary_melter.{module}.simulate', return_value=result), \
                            patch('rotary_melter.Reporting.export_result', return_value=destination) as export, \
                            redirect_stdout(stdout), redirect_stderr(stderr):
                        status = main(['--run', '--engine', engine, '--output', str(destination)])
                    export.assert_called_once_with(result, destination)
                    self.assertEqual(status, expected)
                    self.assertIn(str(destination.resolve()), stdout.getvalue())
                    self.assertEqual('Calculation cancelled.' in stderr.getvalue(), bool(expected))


class AnalysisExitStatusTests(unittest.TestCase):
    def test_cancelled_sizing_exports_before_returning_failure(self):
        result = {'analysis': 'sizing', 'cancelled': True, 'possible': False,
                  'limitKW': 1000, 'reason': 'target not reached'}
        temporary_root = PROJECT_ROOT / '.autodev'
        temporary_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temporary_root) as directory:
            stderr = io.StringIO()
            with patch('rotary_melter.NativeEngine.execute', return_value=result), \
                    redirect_stdout(io.StringIO()), redirect_stderr(stderr):
                status = main(['--analyse', 'sizing', '--output', directory])
            folder = Path(directory)
            self.assertEqual(json.loads((folder / 'analysis.json').read_text(encoding='utf-8')), result)
            self.assertEqual(status, 1)
            self.assertIn('Analysis cancelled.', stderr.getvalue())

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
