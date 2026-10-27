"""Windows desktop host. Local calculations; native Save As; no remote page."""
from __future__ import annotations
import argparse
import base64
import ctypes
import json
import os
from pathlib import Path
import sys
import threading
import traceback
import webview
from .Workspace import WorkspaceStore
from .Paths import resource_path

APP_VERSION = '3.0.0'


class DesktopApi:
    def __init__(self, diagnostic: Path | None = None):
        self._window = None
        self._diagnostic = diagnostic
        self._last_directory = ''
        self._reported = False
        self._motion_jobs = None
        self._demo = None
        from .NativeEngine import NativeJobs
        native_output = diagnostic.parent/'native_runs' if diagnostic else None
        self._native_jobs = NativeJobs(native_output)
        store_path=(diagnostic.parent/'workspace_v20_test.json') if diagnostic else Path(os.environ.get('LOCALAPPDATA',str(Path.home())))/'RotaryMelter'/'workspace.json'
        self._workspace_store=WorkspaceStore(store_path)

    def workspace_load(self):
        try:return {'ok':True,'data':self._workspace_store.read()}
        except Exception as exc:return {'ok':False,'error':str(exc)}

    def native_info(self):
        from .NativeEngine import info
        return info()

    def native_gpu_info(self):
        from .GpuAnalysis import info
        report = info()
        if self._diagnostic:
            (self._diagnostic.parent/'gpu_info.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        return report

    def native_gpu_audit(self, ident: str):
        try:
            from .GpuAnalysis import save_audit
            saved=self._native_jobs.read_result(ident)
            report=save_audit(saved['result'],Path(saved['directory'])/'gpu_analysis')
            return {'ok':True,'result':report,'directory':str(Path(saved['directory'])/'gpu_analysis')}
        except Exception as exc:
            return {'ok':False,'error':str(exc)}

    def native_start(self, task: str, inputs: dict, options: dict | None = None):
        try:
            return self._native_jobs.start(task, inputs, options)
        except Exception as exc:
            return {'ok': False, 'error': str(exc)}

    def native_poll(self, ident: str, sequence: int = -1):
        return self._native_jobs.poll(ident, sequence)

    def native_cancel(self, ident: str):
        return self._native_jobs.cancel(ident)

    def native_history(self):
        return self._native_jobs.history()

    def native_read_run(self, ident: str):
        try:
            return self._native_jobs.read_result(ident)
        except Exception as exc:
            return {'ok': False, 'error': str(exc)}

    def workspace_save(self,data,expected_revision):
        try:return {'ok':True,'revision':self._workspace_store.save(data,expected_revision)}
        except Exception as exc:return {'ok':False,'error':str(exc)}

    def demo_info(self, inputs: dict, settings: dict) -> dict:
        """A computed recording is offered only for its matching initial case."""
        try:
            import numpy as np
            path=resource_path('assets/motion_cpp_record.npz')
            backend='cpp'
            if not path.exists():
                path=resource_path('assets/motion_v18_record.npz')
                backend='v11_numba_reference'
            if not path.exists():return {'ok':True,'available':False,'reason':'not_packaged'}
            if self._demo is None or self._demo.get('path')!=str(path):
                data=np.load(path)
                self._demo={'path':str(path),'backend':backend,'data':data,'inputs':json.loads(str(data['inputs'])),'settings':json.loads(str(data['settings'])),'metadata':json.loads(str(data['metadata'])),'positions':None}
            d=self._demo;keys=['diameter','length','headDepth','heads','angle','rpm','rotationDirection','particle','chargeMode','targetFill','packing','rhos','rhol']
            if inputs.get('chargeMode')==0:keys.append('mass')
            matched=all(abs(float(inputs[k])-float(d['inputs'][k]))<1e-9 for k in keys)
            matched=matched and d['metadata'][-1]['seconds']>=d['settings']['duration']-1e-8
            matched=matched and settings.get('solver')=='rigid' and abs(float(settings.get('liquid',0)))<1e-9
            for k in ['dt','iterations','positionIterations','muWall','muParticle','restitution','settle','duration']:
                matched=matched and abs(float(settings.get(k,d['settings'].get(k,0)))-float(d['settings'].get(k,0 if k not in ['muWall','muParticle','restitution'] else {'muWall':.45,'muParticle':.35,'restitution':.25}[k])))<1e-9
            return {'ok':True,'available':bool(matched),'backend':d['backend'],'reason':'matching_computed_case' if matched else 'case_differs','frameCount':len(d['metadata']),'settings':d['settings'],'first':d['metadata'][0],'last':d['metadata'][-1]}
        except Exception as exc:return {'ok':False,'error':str(exc),'available':False}

    def demo_frames(self, start: int, count: int = 8) -> dict:
        try:
            import numpy as np
            d=self._demo
            if d is None:raise ValueError('Call demo_info first.')
            if d['positions'] is None:d['positions']=d['data']['positions']
            out=[]
            for i in range(max(0,int(start)),min(len(d['metadata']),int(start)+max(1,int(count)))):
                f=dict(d['metadata'][i]);f['positions']=base64.b64encode(np.asarray(d['positions'][i],dtype='<f4').tobytes()).decode('ascii');out.append(f)
            return {'ok':True,'frames':out}
        except Exception as exc:return {'ok':False,'error':str(exc)}

    def start_motion(self, inputs: dict, settings: dict) -> dict:
        try:
            from .dynamics.ContactDynamics import MotionJobs
            if self._motion_jobs is None:
                self._motion_jobs = MotionJobs()
            return self._motion_jobs.start(inputs, settings)
        except Exception as exc:
            return {'ok': False, 'error': str(exc)}

    def poll_motion(self, ident: str, sequence: int = -1) -> dict:
        if self._motion_jobs is None:
            return {'ok': False, 'error': 'No motion job'}
        return self._motion_jobs.poll(ident, sequence)

    def pause_motion(self, paused: bool = True) -> dict:
        return self._motion_jobs.pause(paused) if self._motion_jobs else {'ok': True}

    def stop_motion(self) -> dict:
        return self._motion_jobs.stop() if self._motion_jobs else {'ok': True}

    def independent_compare(self, spec: dict, javascript: dict) -> dict:
        try:
            from .Calculation import compare
            return {'ok': True, 'result': compare(spec, javascript)}
        except Exception as exc:
            return {'ok': False, 'error': str(exc)}

    def native_smoke(self, inputs: dict) -> dict:
        try:
            import numpy as np
            from .dynamics.ContactDynamics import DEM, MotionJobs
            c = dict(inputs)
            c.update(diameter=120, length=160, headDepth=30, targetFill=.3, chargeMode=1)
            m = DEM(c, {'settle': 0})
            before = m.p[:, :3].copy()
            m.advance(60)
            finite = bool(np.isfinite(m.p).all())
            moved = bool(np.max(np.abs(m.p[:, :3] - before)) > 1e-8)
            jobs = MotionJobs()
            ident = jobs.start(c, {'duration': .002, 'settle': 0, 'liquid': .01})['id']
            import time
            deadline = time.monotonic() + 50
            response = None
            while time.monotonic() < deadline:
                response = jobs.poll(ident)
                if response['status'] in ('complete', 'error'):
                    break
                time.sleep(.05)
            threaded = response and response['status'] == 'complete' and response['snapshot'] and np.isfinite(response['snapshot']['liquidPlane'])
            return {'ok': bool(finite and moved and threaded), 'finite': finite, 'moved': moved, 'threadedJob': bool(threaded), 'snapshot': m.snapshot()}
        except Exception as exc:
            return {'ok': False, 'error': str(exc)}

    def set_language(self, language: str) -> dict:
        self._language = 'en' if language == 'en' else 'tr'
        return {'ok': True}

    def save_file(self, filename: str, encoded: str, language: str = 'tr') -> dict:
        try:
            name = Path(filename).name
            extension = Path(name).suffix.lower()
            types = {'.pdf': 'PDF raporu (*.pdf)', '.csv': 'CSV tablosu (*.csv)', '.json': 'JSON girdileri (*.json)', '.md': 'Markdown raporu (*.md)'}
            if language == 'en':
                types = {'.pdf': 'PDF report (*.pdf)', '.csv': 'CSV table (*.csv)', '.json': 'JSON inputs (*.json)', '.md': 'Markdown report (*.md)'}
            if extension not in types:
                raise ValueError('Only PDF, CSV, JSON and Markdown files can be saved.' if language == 'en' else 'Yalnız PDF, CSV, JSON ve Markdown dosyaları kaydedilebilir.')
            if not isinstance(encoded, str) or len(encoded) > 80_000_000:
                raise ValueError('Invalid or oversized file data.' if language == 'en' else 'Dosya verisi geçersiz veya çok büyük.')
            content = base64.b64decode(encoded, validate=True)
            selected = self._window.create_file_dialog(
                webview.FileDialog.SAVE, directory=self._last_directory,
                save_filename=name, file_types=(types[extension],),
            )
            if not selected:
                return {'ok': False, 'cancelled': True}
            selected_path = selected[0] if isinstance(selected, (tuple, list)) else selected
            target = Path(selected_path)
            if not target.suffix:
                target = target.with_suffix(extension)
            target.write_bytes(content)
            self._last_directory = str(target.parent)
            return {'ok': True, 'name': target.name}
        except Exception as exc:
            return {'ok': False, 'error': str(exc)}

    def ready(self, payload: dict) -> dict:
        """App-owned startup/integration signal, also used by --self-test."""
        if self._diagnostic and not self._reported:
            self._reported = True
            self._diagnostic.parent.mkdir(parents=True, exist_ok=True)
            valid = (
                isinstance(payload, dict)
                and payload.get('version') == APP_VERSION
                and payload.get('waterToProductMassFlow') == 0
                and payload.get('calculated') is True
                and payload.get('waterRouteNodes') == 6
                and payload.get('surfaceCells', 0) >= 32
                and payload.get('uiSmoke', {}).get('passed') is True
                and payload.get('uiSmoke', {}).get('motion') is True
                and payload.get('uiSmoke', {}).get('nativeDEM') is True
            )
            self._diagnostic.write_text(json.dumps({
                'ok': valid, 'desktop_version': APP_VERSION,
                'renderer': 'edgechromium', 'frozen': bool(getattr(sys, 'frozen', False)),
                'html_bytes': resource_path('Rotary_Melter.html').stat().st_size,
                'app': payload,
            }, ensure_ascii=False, indent=2), encoding='utf-8')
            threading.Timer(.3, self._window.destroy).start()
        return {'ok': True}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', type=Path)
    parser.add_argument('--require-gpu',action='store_true')
    args = parser.parse_args(argv)
    if args.self_test:
        args.self_test = args.self_test.resolve()
        args.self_test.parent.mkdir(parents=True, exist_ok=True)
    api = DesktopApi(args.self_test)
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('RotaryMelter.Desktop.1')
        html = resource_path('Rotary_Melter.html').read_text(encoding='utf-8')
        if args.require_gpu:
            html=html.replace('<head>','<head><script>window.__MELTER_REQUIRE_GPU__=true;</script>',1)
        if args.self_test:
            html = html.replace('<head>', '''<head><script>window.__MELTER_SELF_TEST__=true;window.__testErrors=[];window.addEventListener('error',e=>{window.__testErrors.push(e.message+' '+e.filename+':'+e.lineno);if(window.pywebview?.api)window.pywebview.api.ready({version:'3.0.0',calculated:false,errors:window.__testErrors});});window.addEventListener('pywebviewready',()=>{if(window.__testErrors.length)window.pywebview.api.ready({version:'3.0.0',calculated:false,errors:window.__testErrors});});</script>''', 1)
        webview.settings['ALLOW_DOWNLOADS'] = False  # Saving goes through the native bridge.
        webview.settings['ALLOW_FILE_URLS'] = False  # All packaged assets are embedded.
        webview.settings['OPEN_EXTERNAL_LINKS_IN_BROWSER'] = True
        api._window = webview.create_window(
            'Rotary Melter Workstation 3.0 - AISI 316 / 2B', html=html, js_api=api,
            width=1440, height=900, min_size=(1000, 650), resizable=True,
            hidden=bool(args.self_test), text_select=True, background_color='#eff4f5',
        )
        timeout = None
        if args.self_test:
            def checkpoint():
                if api._reported:
                    return
                try:
                    state = api._window.evaluate_js("({errors:document.getElementById('errors')?.textContent,message:document.getElementById('nativeMessage')?.textContent,reported:window.RotaryApp?.state.reported,task:window.RotaryApp?.state.task,engine:window.RotaryApp?.state.result?.engine,smokeStage:window.__smokeStage})")
                    (args.self_test.parent/'startup_state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
                except Exception:
                    pass
                timer=threading.Timer(30,checkpoint)
                timer.daemon=True
                timer.start()
            checkpoint_timer=threading.Timer(30,checkpoint)
            checkpoint_timer.daemon=True
            checkpoint_timer.start()
            def expired():
                if not api._reported:
                    args.self_test.write_text(json.dumps({'ok': False, 'error': 'Startup signal timeout'}), encoding='utf-8')
                    api._window.destroy()
            timeout = threading.Timer(300, expired)
            timeout.daemon = True
            timeout.start()
        webview.start(gui='edgechromium', debug=False, private_mode=True)
        if timeout:
            timeout.cancel()
        if args.self_test:
            return 0 if args.self_test.exists() and json.loads(args.self_test.read_text(encoding='utf-8')).get('ok') else 1
        return 0
    except Exception as exc:
        details = traceback.format_exc()
        if args.self_test:
            args.self_test.parent.mkdir(parents=True, exist_ok=True)
            args.self_test.write_text(json.dumps({'ok': False, 'error': str(exc), 'traceback': details}, ensure_ascii=False, indent=2), encoding='utf-8')
        else:
            ctypes.windll.user32.MessageBoxW(None, 'Uygulama açılamadı. Microsoft Edge WebView2 çalışma zamanını kontrol edin.\n\n' + str(exc), 'Rotary Melter Desktop', 0x10)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
