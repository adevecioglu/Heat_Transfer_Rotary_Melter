"""Headless JSON/CSV/HTML export; interactive PDF export remains in web/reporting."""
import csv
import html
import json
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
                '<h1>Rotary Melter — V11 calculation</h1><p>Numerical model results; not experimental validation.</p>'
                '<p><a href="result.json">Full result JSON</a> · <a href="history.csv">History CSV</a></p><table>'+rows+'</table></html>')
    (folder / 'report.html').write_text(document, encoding='utf-8')
    return folder
