"""Rebuild the self-contained desktop interface from its named source modules."""
import base64
import html
import json
from rotary_melter.Paths import PROJECT_ROOT, WEB_DIR, HTML_FILE


def build_interface():
    manifest = json.loads((WEB_DIR / 'manifest.json').read_text(encoding='utf-8'))
    document = (WEB_DIR / 'Interface.template.html').read_text(encoding='utf-8')
    for group in ('ENGINE', 'VIEW', 'REPORT', 'APP'):
        code = '\n'.join((WEB_DIR / name).read_text(encoding='utf-8-sig') for name in manifest[group])
        document = document.replace('@@'+group+'@@', code)
    photos = []
    for name, label in [('vessel_09s.jpg', 'Inclined vessel'), ('shaft_15s.jpg', 'Shaft and drive'), ('joint_21s.jpg', 'Rotary joint')]:
        encoded = base64.b64encode((WEB_DIR / 'assets' / name).read_bytes()).decode('ascii')
        photos.append(f'<figure><img src="data:image/jpeg;base64,{encoded}" alt="{label}"><figcaption>{label}</figcaption></figure>')
    document = document.replace('@@PHOTOS@@', ''.join(photos))
    native = '\n\n'.join('# '+name+'\n'+(PROJECT_ROOT / name).read_text(encoding='utf-8') for name in manifest['nativeSources'])
    document = document.replace('<pre id="executedCode"></pre>', '<pre id="executedCode"></pre><details><summary>Python / NumPy / Numba / SciPy source</summary><pre>'+html.escape(native)+'</pre></details>')
    if '@@' in document:
        raise ValueError('The interface contains an unresolved build token.')
    HTML_FILE.parent.mkdir(parents=True, exist_ok=True)
    HTML_FILE.write_text(document, encoding='utf-8')
    return HTML_FILE


if __name__ == '__main__':
    print(build_interface())
