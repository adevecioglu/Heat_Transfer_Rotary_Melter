"""Headless JSON/CSV/HTML export; interactive PDF export remains in web/reporting."""
import csv
import html
import json
import hashlib
import shutil
from pathlib import Path


REFERENCE_EQUATION_FILES = (
    'rotary_melter/Calculation.py',
    'rotary_melter/web/calculations/Calculation.js',
    'rotary_melter/web/calculations/Convergence.js',
    'rotary_melter/web/calculations/ParticleHeatTransfer.js',
    'docs/history/Motion_Research_v18.md',
    'docs/history/Research_Notes_v17.md',
    'docs/history/Startup_Audit_v22.md',
    'docs/history/Verification_Motion_v18.md',
)


def export_result(result, folder):
    import sys
    from .Paths import resource_path, PROJECT_ROOT

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
    elif (folder / 'history.csv').exists():
        # A reused output directory must not retain samples from an older run.
        (folder / 'history.csv').write_text('', encoding='utf-8')
    summary = {key: value for key, value in result.items() if not isinstance(value, (dict, list))}
    cancelled = bool(result.get('cancelled', False))
    status = 'CANCELLED' if cancelled else 'COMPLETED'
    partial_notice = ' This run was interrupted; its outputs are partial results.' if cancelled else ''
    (folder / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    rows = ''.join(f'<tr><th>{html.escape(key)}</th><td>{html.escape(str(value))}</td></tr>' for key, value in summary.items())
    history_link = (' · <a href="history.csv">History CSV</a>' if history
                    else ' · No time-series samples are available for this run.')
    document = ('<!doctype html><html lang="en"><meta charset="utf-8"><title>Rotary Melter calculation</title>'
                '<style>body{font:16px/1.6 system-ui;max-width:1000px;margin:40px auto;padding:0 24px}'
                'table{border-collapse:collapse;width:100%}th,td{border:1px solid #ccd5df;padding:8px;text-align:left}</style>'
                '<h1>Rotary Melter — calculation run</h1><p>Numerical model results; not experimental validation.</p>'
                f'<p>Status: <strong>{status}</strong>.{partial_notice}</p>'
                '<p><a href="result.json">Full result JSON</a>'+history_link+'</p><table>'+rows+'</table></html>')
    (folder / 'report.html').write_text(document, encoding='utf-8')
    trace = result.get('traceability', {})
    engine = result.get('engine', {})
    native = engine.get('name') == 'Rotary Melter C++'
    catalogue = resource_path('docs/CPP_CALCULATION_EQUATIONS.md' if native
                              else 'docs/CALCULATION_EQUATIONS.md')
    manifest = {
        'runId': trace.get('runId', folder.name), 'createdUtc': trace.get('createdUtc'),
        'inputSha256': trace.get('inputSha256'), 'nativeLibrarySha256': trace.get('nativeLibrarySha256'),
        'sourceFingerprint': engine.get('sourceFingerprint'), 'integrator': engine.get('integrator'),
        'targetReached': result.get('targetReached'), 'seconds': result.get('seconds'),
        'cancelled': cancelled,
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
        ('Status: **CANCELLED**. This run was interrupted; its outputs are partial results.'
         if cancelled else 'Status: **COMPLETED**.'), '',
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
        ('5. Solve the coupled granule surface balance with Eigen; evaluate conductive, convective and radiative rates.'
         if engine.get('name') == 'Rotary Melter C++' else
         '5. Evaluate heat transfer with the retained V11 JavaScript reference implementation.'),
        ('6. Advance the conservative ODE state with the selected Boost.Odeint method; dependent time steps remain sequential.'
         if engine.get('name') == 'Rotary Melter C++' else
         '6. Advance the state with the V11 JavaScript reference time-stepping implementation.'),
        '7. Check energy closure and target status; export fields, time series and provenance.', '',
        ('See the [equation catalogue](EQUATIONS.md) for formulas and source references.'
         if catalogue.is_file() else 'The equation catalogue is unavailable.'), '',
        '## Traceability', '',
        f"- Engine: `{manifest['engine']}`",
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
    if catalogue.is_file():
        frozen = getattr(sys, 'frozen', False)
        equations = catalogue.read_text(encoding='utf-8')
        if native:
            sources = resource_path('native_sources') if frozen else PROJECT_ROOT / 'native'
            if sources.is_dir():
                shutil.copytree(sources, folder / 'source/native', dirs_exist_ok=True)
            equations = equations.replace('(../native/', '(source/native/')
            reference = resource_path('docs/CALCULATION_EQUATIONS.md')
            if reference.is_file():
                _export_reference_catalogue(reference.read_text(encoding='utf-8'),
                                           folder / reference.name, resource_path, frozen)
            (folder / 'EQUATIONS.md').write_text(equations, encoding='utf-8')
        else:
            _export_reference_catalogue(equations, folder / 'EQUATIONS.md', resource_path, frozen)
    return folder


def _export_reference_catalogue(equations, destination, resource_path, frozen):
    for relative in REFERENCE_EQUATION_FILES:
        source = resource_path('reference_sources/' + relative if frozen else relative)
        if source.is_file():
            attachment = destination.parent / 'source' / relative
            attachment.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, attachment)
    equations = equations.replace('(../rotary_melter/', '(source/rotary_melter/')
    equations = equations.replace('(history/', '(source/docs/history/')
    destination.write_text(equations, encoding='utf-8')
