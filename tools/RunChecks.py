"""Run current numerical and integration checks, keeping all logs in outputs."""
import argparse
from datetime import datetime
import json
import os
import subprocess
import sys
from rotary_melter.Paths import PROJECT_ROOT, OUTPUTS_DIR, node_executable


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--desktop', action='store_true', help='Also run the hidden WebView2 integration test')
    parser.add_argument('--skip-native', action='store_true', help='Skip native contact regression checks')
    args = parser.parse_args()
    output = OUTPUTS_DIR / 'checks' / datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    output.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8',
               TEMP=str(output), TMP=str(output), PYTHONPATH=str(PROJECT_ROOT))
    tasks = [('python_workflow', [sys.executable, '-m', 'unittest', 'discover', '-s', str(PROJECT_ROOT/'tests'), '-v'])]
    tasks += [(test.stem, [node_executable(), str(test)]) for test in sorted((PROJECT_ROOT/'tests'/'javascript').glob('test_*.js'))]
    if not args.skip_native:
        tasks += [('native_contacts', [sys.executable, '-m', 'tests.native_motion_checks'])]
    if args.desktop:
        tasks += [('desktop', [sys.executable, str(PROJECT_ROOT/'app.py'), '--self-test', str(output/'desktop.json')])]
    results = []
    for name, command in tasks:
        try:
            result = subprocess.run(command, cwd=output, env=env, capture_output=True, text=True,
                                    encoding='utf-8', timeout=420)
            text = result.stdout+'\n'+result.stderr
            passed = result.returncode == 0
        except subprocess.TimeoutExpired:
            text = 'Timed out after 420 seconds.'
            passed = False
        (output / (name+'.log')).write_text(text, encoding='utf-8')
        results.append({'name': name, 'passed': passed, 'log': name+'.log'})
        print(name+': '+('PASS' if passed else 'FAIL'), flush=True)
        if not passed:
            print(text[-1800:], flush=True)
    report = {'passed': all(item['passed'] for item in results), 'checks': results}
    (output/'results.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('Reports:', output, flush=True)
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
