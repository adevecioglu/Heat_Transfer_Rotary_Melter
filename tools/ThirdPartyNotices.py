"""Collect upstream notices for the pinned native numerical/runtime libraries."""
import hashlib
import json
from .SetupCpp import open_url
from rotary_melter.Paths import PROJECT_ROOT

NOTICES = {
    'Boost-1.90.0.txt': 'https://raw.githubusercontent.com/boostorg/boost/boost-1.90.0/LICENSE_1_0.txt',
    'Eigen-5.0.0-MPL2.txt': 'https://gitlab.com/libeigen/eigen/-/raw/5.0.0/COPYING.MPL2',
    'nlohmann-json-3.12.0.txt': 'https://raw.githubusercontent.com/nlohmann/json/v3.12.0/LICENSE.MIT',
    'CoolProp-IF97-2.2.1.txt': 'https://raw.githubusercontent.com/CoolProp/IF97/v2.2.1/LICENSE',
    'BS-thread-pool-5.1.0.txt': 'https://raw.githubusercontent.com/bshoshany/thread-pool/v5.1.0/LICENSE.txt',
    'GCC-runtime-exception.txt': 'https://raw.githubusercontent.com/gcc-mirror/gcc/releases/gcc-16/COPYING.RUNTIME',
    'GCC-GPL3.txt': 'https://raw.githubusercontent.com/gcc-mirror/gcc/releases/gcc-16/COPYING3',
    'mingw-w64-runtime.txt': 'https://raw.githubusercontent.com/mingw-w64/mingw-w64/v14.0.0/COPYING',
    'winpthreads.txt': 'https://raw.githubusercontent.com/mingw-w64/mingw-w64/v14.0.0/mingw-w64-libraries/winpthreads/COPYING',
}


def collect():
    folder=PROJECT_ROOT/'native'/'third_party_licenses'
    folder.mkdir(parents=True,exist_ok=True)
    manifest={}
    for name,url in NOTICES.items():
        target=folder/name
        if not target.exists():
            with open_url(url,timeout=30) as stream:
                target.write_bytes(stream.read())
        manifest[name]={'url':url,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
        print(name,flush=True)
    (folder/'sources.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    collect()
