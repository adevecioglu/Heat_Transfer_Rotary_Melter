"""Readable numerical-analysis reports with an auditable request/result trail."""
import csv
import hashlib
import json
from pathlib import Path


def export_analysis(result, folder):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)
    (folder / 'analysis.json').write_text(encoded, encoding='utf-8')
    rows = []
    for case in result.get('cases', []):
        values = case.get('summary', {})
        rows.append({'case': case['name'], 'ok': case.get('ok', False),
                     'target_reached': values.get('targetReached'), 'physical_seconds': values.get('seconds'),
                     'core_c': values.get('coreC'), 'input_kwh': values.get('energyInKWh'),
                     'loss_kwh': values.get('lossKWh'), 'relative_energy_residual': values.get('balanceRelative'),
                     'wall_seconds': values.get('wallSeconds'), 'error': case.get('error', '')})
    if rows:
        with (folder / 'analysis.csv').open('w', encoding='utf-8-sig', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    trace = result.get('traceability', {})
    title = result.get('analysis', 'numerical analysis')
    manifest = {'runId': trace.get('runId', folder.name), 'type': 'analysis', 'analysis': title,
                'createdUtc': trace.get('createdUtc'), 'inputSha256': trace.get('inputSha256'),
                'cases': len(rows), 'resultSha256': hashlib.sha256(encoded.encode('utf-8')).hexdigest()}
    (folder/'run_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    lines = [f'# Rotary Melter — {title}', '',
             'Results are model predictions and numerical checks; they are not experimental validation.', '',
             '## Execution and traceability', '',
             f"- Run: `{trace.get('runId', 'command-line')}`",
             f"- Input SHA-256: `{trace.get('inputSha256', 'unavailable')}`",
             f"- Native library SHA-256: `{trace.get('nativeLibrarySha256', 'unavailable')}`",
             f"- Independent-case threads: {result.get('threadsUsed', 1)}",
             f"- Parallel execution: {result.get('parallelism', 'sequential dependent search')}", '',
             '## Measured outputs', '',
             '| Case | Target reached | Physical time (s) | Input energy (kWh) | Relative energy residual | Wall time (s) |',
             '| --- | --- | ---: | ---: | ---: | ---: |']
    for row in rows:
        def fmt(key):
            value = row.get(key)
            return f'{value:.8g}' if isinstance(value, (int, float)) else str(value)
        lines.append(f"| {row['case']} | {row['target_reached']} | {fmt('physical_seconds')} | {fmt('input_kwh')} | {fmt('relative_energy_residual')} | {fmt('wall_seconds')} |")
    if not rows:
        lines += ['', f"Possible: {result.get('possible')}; conditional power: {result.get('kw', 'unavailable')} kW."]
    lines += ['', '## Convergence diagnostics', '', '```json',
              json.dumps({key: result[key] for key in ('targetGci', 'energyGci', 'timeDifferencePercent', 'radialDifferencePercent', 'commonTimeStepSeconds', 'sensitivities') if key in result}, indent=2),
              '```', '', '## Interpretation', '',
              'Convergence cases use a common stable time step to separate spatial and temporal effects. '
              'A target-time difference is meaningful only if both runs reach the target. '
              'A conditional GCI is omitted when differences oscillate, do not contract, or are below time resolution.', '',
              'Thermodynamics, conductance, integration, library use and stage-by-stage formula purposes are documented in '
              '`docs/CPP_CALCULATION_EQUATIONS.md`. The exact scenario and options are embedded in `analysis.json`.', '',
              f'Analysis JSON SHA-256: `{hashlib.sha256(encoded.encode("utf-8")).hexdigest()}`.', '']
    (folder / 'ANALYSIS_REPORT.md').write_text('\n'.join(lines), encoding='utf-8')
    return folder
