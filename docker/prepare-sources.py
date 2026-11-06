#!/usr/bin/env python3
"""Prepare checksum-pinned build inputs and preserve their original notices."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import tarfile
import tempfile
import zipfile


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def prepare(manifest, work, notices):
    spec = json.loads(manifest.read_text())
    require(spec['schema'] == 1, 'unsupported source manifest')
    work.mkdir(parents=True, exist_ok=False)
    notices.mkdir(parents=True, exist_ok=False)
    receipts = []
    for item in spec['sources']:
        relative = PurePosixPath(item['destination'])
        require(not relative.is_absolute() and '..' not in relative.parts,
                'unsafe source destination')
        destination = work / relative
        require(not destination.exists() and not destination.is_symlink(),
                f'source destination exists: {destination}')
        with tempfile.TemporaryDirectory(prefix='fetch-', dir=work) as temporary:
            scratch = Path(temporary)
            archive = scratch / 'download'
            subprocess.run(['curl', '--fail', '--location', '--retry', '3',
                            '--retry-delay', '2', '--connect-timeout', '30',
                            '--max-time', '600', item['url'], '-o', str(archive)], check=True)
            require(digest(archive) == item['sha256'], f'checksum mismatch: {item["name"]}')
            if item['format'] == 'file':
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(archive, destination)
            else:
                unpack = scratch / 'unpacked'
                unpack.mkdir()
                if item['format'] == 'tar':
                    with tarfile.open(archive) as reader:
                        reader.extractall(unpack, filter='data')
                elif item['format'] == 'zip':
                    with zipfile.ZipFile(archive) as reader:
                        for entry in reader.infolist():
                            name = PurePosixPath(entry.filename)
                            require(not name.is_absolute() and '..' not in name.parts,
                                    'unsafe ZIP member')
                            require(not stat.S_ISLNK(entry.external_attr >> 16), 'ZIP symlink')
                        reader.extractall(unpack)
                else:
                    raise RuntimeError('unknown archive format')
                roots = list(unpack.iterdir())
                require(len(roots) == 1 and roots[0].is_dir() and not roots[0].is_symlink(),
                        f'archive must contain one directory: {item["name"]}')
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(roots[0]), destination)
        copied = []
        candidates = [destination] if item['format'] == 'file' else destination.rglob('*')
        for path in sorted(candidates):
            if not path.is_file() or not re.search(r'(license|copying|copyright|notice|^OFL\.)',
                                                   path.name, re.I):
                continue
            require(not path.is_symlink(), f'notice symlink: {path}')
            relative = path.name if item['format'] == 'file' else str(path.relative_to(destination))
            target = notices / item['name'] / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
            copied.append(dict(path=str(target.relative_to(notices)), sha256=digest(target)))
        require(copied or item['name'] == 'comic-font', f'no original notice: {item["name"]}')
        receipts.append(dict(**item, notices=copied))
    source = work / 'rdkit'
    # Reproduce the two upstream download-branch preparation operations that
    # are skipped when pre-extracted, checksum-verified sources are supplied.
    shutil.copyfile(source / 'External/FreeSASA/freesasa2.c',
                    source / 'External/FreeSASA/freesasa-2.0.3/src/freesasa2.c')
    utils = (source / 'Code/cmake/Modules/RDKitUtils.cmake').read_text()
    function = re.search(r'function\(patchCoordGenMaeExportHeaders keyword path\).*?'
                         r'endfunction\(patchCoordGenMaeExportHeaders\)', utils, re.S)
    require(function, 'upstream MAE preparation function missing')
    invocation = work / 'upstream-mae-prepare.cmake'
    invocation.write_text(function.group(0) + '\npatchCoordGenMaeExportHeaders("MAEPARSER" "' +
                          str(source / 'External/CoordGen/maeparser/MaeParserConfig.hpp') + '")\n')
    subprocess.run(['cmake', '-P', str(invocation)], check=True)
    (notices / 'inventory.json').write_text(json.dumps(dict(schema=1,
        upstream_commit=spec['upstream_commit'], sources=receipts), indent=2) + '\n')
    verify(notices)


def verify(root):
    spec = json.loads((root / 'inventory.json').read_text())
    require(spec['schema'] == 1 and len(spec['sources']) == 13, 'incomplete source inventory')
    for item in spec['sources']:
        require(item['notices'] or item['name'] == 'comic-font', 'missing source notice')
        for entry in item['notices']:
            path = root / entry['path']
            require(path.resolve().is_relative_to(root.resolve()) and not path.is_symlink(),
                    'unsafe notice path')
            require(digest(path) == entry['sha256'], f'notice mismatch: {entry["path"]}')
    print('PASS checksum-pinned source notice inventory', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    build = sub.add_parser('prepare')
    build.add_argument('manifest', type=Path)
    build.add_argument('work', type=Path)
    build.add_argument('notices', type=Path)
    check = sub.add_parser('verify')
    check.add_argument('notices', type=Path)
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.manifest, args.work, args.notices)
    else:
        verify(args.notices)
