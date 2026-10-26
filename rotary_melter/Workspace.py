"""Atomic, revision-checked local project storage; no simulation state is restored."""
from pathlib import Path
from contextlib import contextmanager
import json,os,tempfile,threading

SCHEMA='rotary-melter-workspace-1'

def validate(data):
    if not isinstance(data,dict) or data.get('schema')!=SCHEMA:raise ValueError('Unsupported workspace schema')
    cases=data.get('cases')
    if not isinstance(cases,list) or len(cases)>500:raise ValueError('Invalid scenario list (maximum 500)')
    seen=set()
    for case in cases:
        if not isinstance(case,dict):raise ValueError('Invalid scenario')
        ident=case.get('id');name=case.get('name');notes=case.get('notes','')
        if not isinstance(ident,str) or not 1<=len(ident)<=100 or ident in seen:raise ValueError('Invalid or duplicate scenario id')
        seen.add(ident)
        if not isinstance(name,str) or not 1<=len(name.strip())<=120:raise ValueError('Invalid scenario name')
        if not isinstance(notes,str) or len(notes)>4000 or not isinstance(case.get('inputs'),dict):raise ValueError('Invalid scenario inputs or notes')
    if data.get('draft') is not None and not isinstance(data['draft'],dict):raise ValueError('Invalid draft')
    encoded=json.dumps(data,ensure_ascii=False,allow_nan=False)
    if len(encoded.encode('utf-8'))>8_000_000:raise ValueError('Workspace exceeds 8 MB')
    return data

class WorkspaceStore:
    def __init__(self,path):self.path=Path(path);self._mutex=threading.RLock()
    @contextmanager
    def locked(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self._mutex,open(self.path.with_suffix('.lock'),'a+b') as lock:
            lock.seek(0,2)
            if lock.tell()==0:lock.write(b'0');lock.flush()
            lock.seek(0)
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(lock.fileno(),msvcrt.LK_LOCK,1)
            try:yield
            finally:
                if os.name=='nt':lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
    def _read(self):
        if not self.path.exists():return {'schema':SCHEMA,'revision':0,'cases':[],'draft':None}
        if self.path.stat().st_size>8_000_000:raise ValueError('Workspace exceeds 8 MB')
        data=validate(json.loads(self.path.read_text(encoding='utf-8')))
        if not isinstance(data.get('revision'),int) or data['revision']<0:raise ValueError('Invalid revision')
        return data
    def read(self):
        with self.locked():return self._read()
    def save(self,data,expected):
        validate(data)
        with self.locked():
            current=self._read()
            if expected!=current['revision']:raise ValueError('Workspace changed in another window; reload it before saving.')
            output={**data,'revision':current['revision']+1}
            content=json.dumps(output,ensure_ascii=False,indent=2,allow_nan=False)
            fd,temp=tempfile.mkstemp(prefix='workspace_',suffix='.tmp',dir=self.path.parent)
            try:
                with os.fdopen(fd,'w',encoding='utf-8') as stream:stream.write(content);stream.flush();os.fsync(stream.fileno())
                os.replace(temp,self.path)
            finally:
                if os.path.exists(temp):os.unlink(temp)
            return output['revision']
