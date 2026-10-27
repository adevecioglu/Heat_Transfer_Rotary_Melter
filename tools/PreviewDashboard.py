"""Local-only visual QA of the desktop HTML with real C++ calculations.

Uses isolated workspace/run storage under outputs. Native dialogs are excluded;
this development preview is not a replacement for packaged desktop checks.
"""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import secrets
from .BuildInterface import build_interface
from rotary_melter.Interface import DesktopApi
from rotary_melter.Paths import OUTPUTS_DIR


def main(port=8765):
    directory=OUTPUTS_DIR/'dashboard_preview'
    directory.mkdir(parents=True,exist_ok=True)
    host_api=DesktopApi(directory/'preview.json')
    names=['native_info','native_start','native_poll','native_cancel','native_history','native_read_run',
           'workspace_load','workspace_save','demo_info','demo_frames','start_motion','poll_motion',
           'pause_motion','stop_motion','independent_compare','set_language','ready','save_file']
    token=secrets.token_urlsafe(32)
    origin=f'http://127.0.0.1:{port}'
    bridge='''<script>
    window.pywebview={api:Object.fromEntries(NAMES.map(name=>[name,async(...args)=>{
      const response=await fetch('/api/'+name,{method:'POST',headers:{'Content-Type':'application/json','X-Preview-Token':TOKEN},body:JSON.stringify(args)});
      if(!response.ok)throw Error('Preview API HTTP '+response.status);
      return response.json();
    }]))};
    window.addEventListener('load',()=>window.dispatchEvent(new Event('pywebviewready')));
    </script>'''.replace('NAMES',json.dumps(names)).replace('TOKEN',json.dumps(token))
    document=build_interface().read_text(encoding='utf-8').replace('<head>','<head>'+bridge,1).encode('utf-8')

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path!='/':
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header('Content-Type','text/html; charset=utf-8')
            self.send_header('Content-Length',str(len(document)))
            self.end_headers()
            self.wfile.write(document)

        def do_POST(self):
            name=self.path.removeprefix('/api/')
            length=int(self.headers.get('Content-Length','0'))
            if name not in names or self.headers.get('Origin')!=origin or self.headers.get('X-Preview-Token')!=token:
                self.send_error(403)
                return
            if self.headers.get('Content-Type')!='application/json' or not 0<length<=16_000_000:
                self.send_error(400)
                return
            try:
                args=json.loads(self.rfile.read(length))
                if name=='ready':
                    result={'ok':True}
                elif name=='save_file':
                    result={'ok':False,'error':'Native Save As is available in the desktop application.'}
                else:
                    result=getattr(host_api,name)(*args)
            except Exception as error:
                result={'ok':False,'error':str(error)}
            body=json.dumps(result,ensure_ascii=False,allow_nan=False).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type','application/json; charset=utf-8')
            self.send_header('Content-Length',str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self,*args):
            pass

    print('Isolated dashboard preview: '+origin,flush=True)
    with ThreadingHTTPServer(('127.0.0.1',port),Handler) as server:
        server.serve_forever()


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--port',type=int,default=8765)
    main(parser.parse_args().port)
