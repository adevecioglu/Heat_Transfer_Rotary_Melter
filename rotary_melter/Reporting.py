"""Headless JSON/CSV/HTML export; interactive PDF export remains in web/reporting."""
import csv
import html
import json
import hashlib
import shutil
from pathlib import Path


def export_result(result, folder):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    history = result.get('hist', [])
    if history:
        columns = list(dict.fromkeys(key for row in history for key in row))
        with (folder / 'history.csv').open('w', encoding='utf-8-sig', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=columns)
            writer.writeheader()
            for row in history:
                writer.writerow({key: json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value
                                 for key, value in row.items()})
    summary = {key: value for key, value in result.items() if not isinstance(value, (dict, list))}
    (folder / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    rows = ''.join(f'<tr><th>{html.escape(key)}</th><td>{html.escape(str(value))}</td></tr>' for key, value in summary.items())
    document = ('<!doctype html><html lang="en"><meta charset="utf-8"><title>Rotary Melter calculation</title>'
                '<style>body{font:16px/1.6 system-ui;max-width:1000px;margin:40px auto;padding:0 24px}'
                'table{border-collapse:collapse;width:100%}th,td{border:1px solid #ccd5df;padding:8px;text-align:left}</style>'
                '<h1>Rotary Melter — calculation run</h1><p>Numerical model results; not experimental validation.</p>'
                '<p><a href="result.json">Full result JSON</a> · <a href="history.csv">History CSV</a></p><table>'+rows+'</table></html>')
    (folder / 'report.html').write_text(document, encoding='utf-8')
    trace = result.get('traceability', {})
    engine = result.get('engine', {})
    manifest = {
        'runId': trace.get('runId', folder.name), 'createdUtc': trace.get('createdUtc'),
        'inputSha256': trace.get('inputSha256'), 'nativeLibrarySha256': trace.get('nativeLibrarySha256'),
        'sourceFingerprint': engine.get('sourceFingerprint'), 'integrator': engine.get('integrator'),
        'targetReached': result.get('targetReached'), 'seconds': result.get('seconds'),
        'energyInKWh': result.get('energyInKWh'), 'balanceRelative': result.get('balanceRelative'),
        'engine': engine.get('name', 'V11 JavaScript reference'),
        'resultSha256': hashlib.sha256((folder/'result.json').read_bytes()).hexdigest(),
    }
    (folder/'run_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    def number(key):
        value = result.get(key)
        return f'{value:.10g}' if isinstance(value, (float, int)) else str(value)
    markdown = [
        '# Rotary Melter — calculation run', '',
        '## Result', '',
        '| Quantity | Value |', '| --- | ---: |',
        f"| Target reached | {result.get('targetReached')} |",
        f"| Physical duration (s) | {number('seconds')} |",
        f"| Input energy (kWh) | {number('energyInKWh')} |",
        f"| Product energy increase (kWh) | {number('storedProductKWh')} |",
        f"| Heat loss (kWh) | {number('lossKWh')} |",
        f"| Relative energy residual | {number('balanceRelative')} |", '',
        '## Method and stage-by-stage purpose', '',
        '1. Validate numerical inputs and convert engineering dimensions to SI.',
        '2. Build cylinder/head geometry and inclined wet-area tables.',
        '3. Assemble metal/water capacities and radial granule masses.',
        '4. Convert product energy to temperature/liquid fraction using the documented enthalpy law.',
        '5. Solve the coupled granule surface balance with Eigen; evaluate conductive, convective and radiative rates.',
        '6. Advance the conservative ODE state with the selected Boost.Odeint method; dependent time steps remain sequential.',
        '7. Check energy closure and target status; export fields, time series and provenance.', '',
        'The exact C++ formulas, library roles, assumptions, source-line links and literature are in '
        '`docs/CPP_CALCULATION_EQUATIONS.md`. The V11 reference equations remain in `docs/CALCULATION_EQUATIONS.md`.', '',
        '## Traceability', '',
        f"- Run ID: `{manifest['runId']}`",
        f"- Input SHA-256: `{manifest['inputSha256']}`",
        f"- Native library SHA-256: `{manifest['nativeLibrarySha256']}`",
        f"- Native source fingerprint: `{manifest['sourceFingerprint']}`",
        f"- Result JSON SHA-256: `{manifest['resultSha256']}`",
        f"- Integrator: `{manifest['integrator']}`",
        f"- Library versions: `{json.dumps(engine.get('libraries', {}), ensure_ascii=False)}`", '',
        'The complete requested inputs and solver options are embedded in `result.json`. '
        'Run artifacts are calculations, not experimental equipment validation.', '',
    ]
    (folder/'RUN_REPORT.md').write_text('\n'.join(markdown), encoding='utf-8')
    from .Paths import resource_path, PROJECT_ROOT
    catalogue=resource_path('docs/CPP_CALCULATION_EQUATIONS.md')
    if catalogue.is_file():
        import sys
        sources=resource_path('native_sources') if getattr(sys,'frozen',False) else PROJECT_ROOT/'native'
        if sources.is_dir():
            shutil.copytree(sources,folder/'source/native',dirs_exist_ok=True)
        (folder/'EQUATIONS.md').write_text(catalogue.read_text(encoding='utf-8').replace('(../native/','(source/native/'),encoding='utf-8')
    return folder
