"""Configure and build the C++ calculation library and standalone CLI."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from rotary_melter.Paths import PROJECT_ROOT, OUTPUTS_DIR
from .SetupCpp import setup


def source_fingerprint():
    digest=hashlib.sha256()
    for path in sorted((PROJECT_ROOT/'native').rglob('*')):
        if path.is_file() and path.suffix in ('.cpp','.hpp','.h','.json','.txt'):
            digest.update(str(path.relative_to(PROJECT_ROOT)).replace('\\','/').encode()+b'\0'+path.read_text(encoding='utf-8-sig').encode('utf-8'))
    return digest.hexdigest()


def build(build_type='Release',jobs=2):
    setup(compiler=os.name=='nt')
    directory=OUTPUTS_DIR/'native'
    directory.mkdir(parents=True,exist_ok=True)
    scripts=Path(sys.executable).parent
    local_cmake=scripts/('cmake.exe' if os.name=='nt' else 'cmake')
    local_ninja=scripts/('ninja.exe' if os.name=='nt' else 'ninja')
    cmake=str(local_cmake) if local_cmake.exists() else shutil.which('cmake') or 'cmake'
    ninja=str(local_ninja) if local_ninja.exists() else shutil.which('ninja') or 'ninja'
    env=dict(os.environ)
    compiler=PROJECT_ROOT/'.tools/mingw64/bin/g++.exe'
    args=[cmake,'-S',str(PROJECT_ROOT/'native'),'-B',str(directory),'-G','Ninja',
          '-DCMAKE_BUILD_TYPE='+build_type,'-DCMAKE_MAKE_PROGRAM='+ninja,
          '-DROTARY_SOURCE_FINGERPRINT='+source_fingerprint()]
    if os.name=='nt' and compiler.exists():
        args+=['-DCMAKE_CXX_COMPILER='+str(compiler)]
        env['PATH']=str(compiler.parent)+os.pathsep+env['PATH']
    subprocess.run(args,cwd=PROJECT_ROOT,env=env,check=True)
    subprocess.run([cmake,'--build',str(directory),'--parallel',str(jobs)],cwd=PROJECT_ROOT,env=env,check=True)
    binary=directory/'bin'
    if os.name=='nt':
        # Copy the actual dependency closure; runtime names change between GCC releases.
        inspector=compiler.parent/'objdump.exe'
        queue=list(binary.glob('rotary_melter_native.dll'))+list(binary.glob('rotary_melter_cpp.exe'))
        inspected=set()
        while queue:
            current=queue.pop()
            if current.name.lower() in inspected:continue
            inspected.add(current.name.lower())
            description=subprocess.check_output([str(inspector),'-p',str(current)],env=env,text=True,errors='replace')
            for name in re.findall(r'DLL Name:\s*(\S+)',description):
                source=compiler.parent/name
                if source.exists():
                    target=binary/name
                    if not target.exists() or hashlib.sha256(source.read_bytes()).digest()!=hashlib.sha256(target.read_bytes()).digest():
                        shutil.copy2(source,target)
                    queue.append(target)
    manifest={'sourceFingerprint':source_fingerprint(),'type':build_type,'python':sys.version,
              'compiler':subprocess.check_output([str(compiler) if compiler.exists() else 'c++','--version'],env=env,text=True).splitlines()[0]}
    manifest['runtimeFiles']=sorted(inspected) if os.name=='nt' else ['librotary_melter_native.so']
    (directory/'build_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print('Native output:',binary,flush=True)
    return binary


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--debug',action='store_true')
    parser.add_argument('--jobs',type=int,default=2)
    args=parser.parse_args()
    build('Debug' if args.debug else 'Release',args.jobs)
