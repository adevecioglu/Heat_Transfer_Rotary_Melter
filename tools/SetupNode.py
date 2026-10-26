"""Install a checksum-verified, project-local Windows Node.js LTS runtime."""
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile
import hashlib
import os
import shutil
from rotary_melter.Paths import PROJECT_ROOT, OUTPUTS_DIR


def main():
    local = PROJECT_ROOT / '.tools' / 'node' / 'node.exe'
    if local.is_file():
        print(local)
        return 0
    existing = shutil.which('node')
    if existing:
        print('Using installed Node.js:', existing)
        return 0
    if os.name != 'nt':
        raise RuntimeError('Install Node.js 24 LTS for this platform before running checks.')
    base = 'https://nodejs.org/dist/latest-v24.x/'
    with urlopen(base+'SHASUMS256.txt', timeout=45) as response:
        records = response.read().decode('ascii').splitlines()
    expected, name = next(line.split() for line in records if line.endswith('-win-x64.zip'))
    work = OUTPUTS_DIR / 'setup'
    work.mkdir(parents=True, exist_ok=True)
    archive = work / name
    with urlopen(base+name, timeout=120) as response:
        archive.write_bytes(response.read())
    if hashlib.sha256(archive.read_bytes()).hexdigest() != expected:
        raise ValueError('Node.js download checksum mismatch.')
    destination = local.parent.resolve()
    prefix = name.removesuffix('.zip') + '/'
    with ZipFile(archive) as zipped:
        for member in zipped.infolist():
            if member.is_dir():
                continue
            target = (destination / member.filename.removeprefix(prefix)).resolve()
            if not target.is_relative_to(destination):
                raise ValueError('Unsafe runtime archive member.')
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(zipped.read(member))
    print('Installed and SHA-256 verified:', name)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
