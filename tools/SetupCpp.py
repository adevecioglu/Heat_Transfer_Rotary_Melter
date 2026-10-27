"""Fetch pinned numerical headers and a portable compiler inside this project.

Downloads are kept in outputs/cpp_setup. Libraries and tools live in .tools;
the checked-in lock file records exact URLs and SHA-256 digests.
"""
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError
from zipfile import ZipFile
import argparse
import hashlib
import json
import os
import shutil
import tarfile
import time
from rotary_melter.Paths import PROJECT_ROOT, OUTPUTS_DIR

LIBRARIES = {
    'boost': ('1.90.0', 'https://archives.boost.io/release/1.90.0/source/boost_1_90_0.tar.bz2', 'boost'),
    'eigen': ('5.0.0', 'https://gitlab.com/libeigen/eigen/-/archive/5.0.0/eigen-5.0.0.tar.gz', 'eigen'),
    'json': ('3.12.0', 'https://raw.githubusercontent.com/nlohmann/json/v3.12.0/single_include/nlohmann/json.hpp', 'nlohmann/json.hpp'),
    'if97': ('2.2.1', 'https://raw.githubusercontent.com/CoolProp/IF97/v2.2.1/IF97.h', 'IF97.h'),
    'thread_pool': ('5.1.0', 'https://raw.githubusercontent.com/bshoshany/thread-pool/v5.1.0/include/BS_thread_pool.hpp', 'BS_thread_pool.hpp'),
}


def open_url(url, timeout=180):
    for attempt in range(5):
        try:
            return urlopen(Request(url, headers={'User-Agent': 'Rotary-Melter-Native-Setup'}), timeout=timeout)
        except URLError:
            if attempt == 4:
                raise
            time.sleep(min(5, .7 * 2**attempt))


def fetch(url, target, expected=None):
    if not target.exists():
        print('Downloading:', target.name, flush=True)
        with open_url(url) as response:
            target.write_bytes(response.read())
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    if expected and digest != expected:
        raise ValueError('SHA-256 mismatch: '+target.name)
    return digest


def extract_library(archive, destination, kind):
    with tarfile.open(archive) as package:
        for member in package:
            if not member.isfile():
                continue
            parts = Path(member.name).parts[1:]
            if not parts:
                continue
            if kind == 'boost' and parts[0] not in ('boost', 'LICENSE_1_0.txt'):
                continue
            if kind == 'eigen' and parts[0] not in ('Eigen', 'unsupported', 'COPYING.MPL2', 'COPYING.BSD', 'COPYING.README'):
                continue
            target = (destination / Path(*parts)).resolve()
            if not target.is_relative_to(destination.resolve()):
                raise ValueError('Unsafe library archive member.')
            target.parent.mkdir(parents=True, exist_ok=True)
            with package.extractfile(member) as stream:
                target.write_bytes(stream.read())


def setup(compiler=False):
    work = OUTPUTS_DIR / 'cpp_setup'
    work.mkdir(parents=True, exist_ok=True)
    includes = PROJECT_ROOT / '.tools' / 'cpp_deps'
    includes.mkdir(parents=True, exist_ok=True)
    lock_path = PROJECT_ROOT / 'native' / 'dependencies.lock.json'
    lock = json.loads(lock_path.read_text(encoding='utf-8')) if lock_path.exists() else {}
    for name, (version, url, relative) in LIBRARIES.items():
        if (includes / (name+'.complete')).exists():
            continue
        target = work / (name+'-'+version+('.tar.bz2' if name == 'boost' else '.tar.gz' if name == 'eigen' else '.hpp'))
        expected = lock.get(name, {}).get('sha256')
        if name == 'boost' and not expected:
            with open_url(url+'.json', timeout=30) as response:
                expected = json.load(response)['sha256']
        digest = fetch(url, target, expected)
        if name in ('boost', 'eigen'):
            extract_library(target, includes if name == 'boost' else includes/'eigen', name)
        else:
            installed = includes / relative
            installed.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, installed)
        lock[name] = {'version': version, 'url': url, 'sha256': digest}
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_path.write_text(json.dumps(lock, indent=2)+'\n', encoding='utf-8')
        (includes / (name+'.complete')).write_text(digest, encoding='ascii')
        print('Ready:', name, version, flush=True)
    if compiler and os.name == 'nt' and not (PROJECT_ROOT/'.tools/mingw64/bin/g++.exe').exists():
        package = lock.get('windows_compiler')
        if not package:
            with urlopen(Request('https://api.github.com/repos/brechtsanders/winlibs_mingw/releases/latest', headers={'User-Agent': 'Rotary-Melter-Native-Setup'}), timeout=30) as response:
                release = json.load(response)
            asset = next(item for item in release['assets'] if item['name'].endswith('.zip') and 'x86_64' in item['name'] and 'ucrt' in item['name'] and 'llvm' not in item['name'])
            package = {'version': release['tag_name'], 'url': asset['browser_download_url'], 'name': asset['name']}
            if asset.get('digest'):
                package['sha256'] = asset['digest'].removeprefix('sha256:')
        archive = work / package['name']
        package['sha256'] = fetch(package['url'], archive, package.get('sha256'))
        destination = (PROJECT_ROOT / '.tools').resolve()
        with ZipFile(archive) as zipped:
            for member in zipped.infolist():
                if member.is_dir():
                    continue
                target = (destination/member.filename).resolve()
                if not target.is_relative_to(destination):
                    raise ValueError('Unsafe compiler archive member.')
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(zipped.read(member))
        lock['windows_compiler'] = package
        lock_path.write_text(json.dumps(lock, indent=2)+'\n', encoding='utf-8')
        print('Portable GCC ready:', package['version'], flush=True)
    return includes


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--compiler', action='store_true')
    args = parser.parse_args()
    setup(args.compiler)
