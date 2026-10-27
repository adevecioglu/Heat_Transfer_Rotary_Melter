"""Typed, cancellable access to the C++ calculation library.

Python only transports JSON, callbacks and artifacts. Thermal calculations and
independent-case scheduling execute in the native library.
"""
from datetime import datetime, timezone
from pathlib import Path
import ctypes
import hashlib
import json
import os
import re
import sys
import threading
import uuid

from .Paths import PROJECT_ROOT, OUTPUTS_DIR

_PROGRESS = ctypes.CFUNCTYPE(None, ctypes.c_char_p, ctypes.c_void_p)
_CANCEL = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p)
_library = None
_library_path = None
_library_digest = None
_load_lock = threading.Lock()
_dll_directories = []


def library_path():
    override = os.environ.get('ROTARY_MELTER_NATIVE_LIBRARY')
    if override:
        return Path(override).resolve()
    filename = 'rotary_melter_native.dll' if os.name == 'nt' else 'librotary_melter_native.so'
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS) / 'native' / filename
    return OUTPUTS_DIR / 'native' / 'bin' / filename


def _load():
    global _library, _library_path, _library_digest
    with _load_lock:
        if _library is not None:
            return _library
        path = library_path()
        if not path.is_file():
            raise RuntimeError('C++ engine is not built. Run KURULUM.cmd or python -m tools.BuildCpp in the local environment.')
        if os.name == 'nt':
            _dll_directories.append(os.add_dll_directory(str(path.parent)))
        native = ctypes.CDLL(str(path))
        native.rotary_abi_version.restype = ctypes.c_uint
        if native.rotary_abi_version() != 1:
            raise RuntimeError('The native engine ABI is incompatible with this application.')
        native.rotary_execute_json.argtypes = [ctypes.c_char_p, _PROGRESS, _CANCEL, ctypes.c_void_p]
        native.rotary_execute_json.restype = ctypes.c_void_p
        native.rotary_free_json.argtypes = [ctypes.c_void_p]
        native.rotary_free_json.restype = None
        _library_path = path
        _library_digest = hashlib.sha256(path.read_bytes()).hexdigest()
        _library = native
        return native


def execute(request, progress=None, cancelled=None):
    """Execute without holding the GIL; callback lifetimes cover the native call."""
    native = _load()
    errors = []

    def notify(encoded, context):
        try:
            if progress:
                progress(json.loads(encoded.decode('utf-8')))
        except Exception as error:
            errors.append(error)

    def stop(context):
        try:
            return int(bool(errors) or bool(cancelled and cancelled()))
        except Exception as error:
            errors.append(error)
            return 1

    progress_callback, cancel_callback = _PROGRESS(notify), _CANCEL(stop)
    canonical = json.dumps(request, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(',', ':'))
    response = native.rotary_execute_json(canonical.encode('utf-8'), progress_callback, cancel_callback, None)
    if not response:
        raise RuntimeError('The C++ engine returned no response.')
    try:
        envelope = json.loads(ctypes.string_at(response).decode('utf-8'))
    finally:
        native.rotary_free_json(response)
    if errors:
        raise RuntimeError('A calculation callback failed: '+str(errors[0])) from errors[0]
    if not envelope.get('ok'):
        raise RuntimeError(envelope.get('error', 'C++ calculation failed.'))
    result = envelope['result']
    if request.get('action', 'simulate') not in ('info', 'geometry', 'hydraulics', 'water_properties'):
        configuration = request.get('configuration', request)
        encoded = json.dumps(configuration, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode('utf-8')
        result['traceability'] = {
            'inputSha256': hashlib.sha256(encoded).hexdigest(),
            'requestSha256': hashlib.sha256(canonical.encode('utf-8')).hexdigest(),
            'nativeLibrarySha256': _library_digest,
            'createdUtc': datetime.now(timezone.utc).isoformat(),
            'inputEncoding': 'UTF-8 JSON; sorted keys; compact separators; original numeric representation',
            'requestedConfiguration': configuration,
            'options': request.get('options', {}),
        }
    return result


def info():
    try:
        return {'available': True, **execute({'action': 'info'}), 'library': str(library_path())}
    except (OSError, RuntimeError) as error:
        return {'available': False, 'error': str(error)}


def simulate(configuration, no_history=False, options=None, progress=None, cancelled=None):
    settings = dict(options or {}, noHistory=no_history)
    return execute({'action': 'simulate', 'configuration': configuration, 'options': settings}, progress, cancelled)


class NativeJobs:
    """Isolated jobs with cancellation, compact progress and persisted run provenance."""
    def __init__(self, output_directory=None):
        self.output_directory = Path(output_directory) if output_directory else OUTPUTS_DIR / 'runs'
        self._lock = threading.RLock()
        self._jobs = {}

    def start(self, task, configuration, options=None):
        if task not in ('solve', 'verify', 'rpm', 'sizing', 'sensitivity'):
            raise ValueError('Unknown calculation task.')
        _load()
        # Own an immutable request snapshot before the worker crosses threads.
        request = json.loads(json.dumps({'configuration': configuration, 'options': dict(options or {})}, allow_nan=False))
        if task == 'solve':
            request['action'] = 'simulate'
        else:
            request.update(action='analyse', analysis={'verify': 'convergence'}.get(task, task))
        ident = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_') + uuid.uuid4().hex[:10]
        job = {'id': ident, 'task': task, 'status': 'running', 'sequence': 0,
               'progress': {}, 'cancel': threading.Event(), 'result': None, 'error': None}
        with self._lock:
            active = [item for item in self._jobs.values() if item['status'] == 'running']
            if len(active) >= 2:
                raise RuntimeError('Two calculations are already active. Stop one before starting another.')
            terminal = [key for key, item in self._jobs.items() if item['status'] != 'running']
            for key in terminal[:-12]:
                del self._jobs[key]
            self._jobs[ident] = job

        def progress(data):
            with self._lock:
                job['progress'] = data
                job['sequence'] += 1

        def run():
            try:
                result = execute(request, progress, job['cancel'].is_set)
                result.setdefault('traceability', {})['runId'] = ident
                if task == 'solve':
                    from .Reporting import export_result
                    directory = export_result(result, self.output_directory / ident)
                else:
                    from .AnalysisReporting import export_analysis
                    directory = export_analysis(result, self.output_directory / ident)
                with self._lock:
                    job['result'] = result
                    job['directory'] = str(directory.resolve())
                    job['status'] = 'cancelled' if job['cancel'].is_set() or result.get('cancelled') else 'complete'
                    job['sequence'] += 1
            except Exception as error:
                with self._lock:
                    job['error'] = str(error)
                    job['status'] = 'cancelled' if job['cancel'].is_set() else 'error'
                    job['sequence'] += 1

        worker = threading.Thread(target=run, name='cpp-'+ident, daemon=True)
        job['thread'] = worker
        worker.start()
        return {'ok': True, 'id': ident, 'task': task}

    def poll(self, ident, sequence=-1):
        with self._lock:
            job = self._jobs.get(ident)
            if not job:
                return {'ok': False, 'error': 'Unknown calculation job.'}
            data = {key: job[key] for key in ('id', 'task', 'status', 'sequence')}
            data['ok'] = True
            if sequence != job['sequence']:
                data['progress'] = job['progress']
                if job['status'] == 'complete':
                    data.update(result=job['result'], directory=job.get('directory'))
                if job['error']:
                    data['error'] = job['error']
            return data

    def cancel(self, ident):
        with self._lock:
            job = self._jobs.get(ident)
            if not job:
                return {'ok': False, 'error': 'Unknown calculation job.'}
            if job['status'] == 'running':
                job['cancel'].set()
            return {'ok': True, 'id': ident}

    def history(self, limit=12):
        if not self.output_directory.exists():
            return {'ok': True, 'runs': []}
        records = []
        for directory in sorted(self.output_directory.iterdir(), key=lambda item: item.name, reverse=True)[:100]:
            manifest = directory/'run_manifest.json'
            if manifest.is_file():
                try:
                    records.append(json.loads(manifest.read_text(encoding='utf-8')))
                except (OSError, ValueError):
                    continue
            if len(records) >= max(1, min(int(limit), 30)):
                break
        return {'ok': True, 'runs': records}

    def read_result(self, ident):
        if not isinstance(ident, str) or not re.fullmatch(r'[A-Za-z0-9_\-]{1,100}', ident):
            raise ValueError('Invalid run identifier.')
        directory = (self.output_directory/ident).resolve()
        if not directory.is_relative_to(self.output_directory.resolve()):
            raise ValueError('Invalid run location.')
        path = directory/'result.json'
        if not path.is_file():
            path = directory/'analysis.json'
        if not path.is_file():
            raise ValueError('The selected run is not available.')
        if path.stat().st_size > 150_000_000:
            raise ValueError('The selected result is too large for interactive replay.')
        return {'ok': True, 'result': json.loads(path.read_text(encoding='utf-8')), 'directory': str(directory)}
