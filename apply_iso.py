"""Build a translated copy of the matching .hack//Infection SLUS-20267 ISO."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile

SECTOR = 2048

def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def read_directory(f, lba, size):
    if size <= 0 or size > 16 * 1024 * 1024:
        raise ValueError('Unexpected directory size.')
    f.seek(lba * SECTOR)
    data = f.read(size)
    if len(data) != size:
        raise ValueError('Truncated directory.')
    records = []
    pos = 0
    while pos < size:
        length = data[pos]
        if not length:
            pos = (pos // SECTOR + 1) * SECTOR
            continue
        rec = data[pos:pos + length]
        if len(rec) != length or length < 34 or 33 + rec[32] > length:
            raise ValueError('Malformed ISO9660 directory record.')
        name = rec[33:33 + rec[32]].split(b';')[0]
        if name not in (b'\0', b'\1'):
            if rec[1] or rec[25] & 0x80 or rec[26] or rec[27]:
                raise ValueError('Unsupported ISO file layout.')
            records.append((name, struct.unpack_from('<I', rec, 2)[0],
                            struct.unpack_from('<I', rec, 10)[0], bool(rec[25] & 2)))
        pos += length
    return records

def find_file(f, parts):
    f.seek(16 * SECTOR)
    pvd = f.read(SECTOR)
    if pvd[:7] != b'\x01CD001\x01' or struct.unpack_from('<H', pvd, 128)[0] != SECTOR:
        raise ValueError('Expected a 2048-byte-sector ISO9660 image.')
    lba = struct.unpack_from('<I', pvd, 158)[0]
    size = struct.unpack_from('<I', pvd, 166)[0]
    for i, part in enumerate(parts):
        matches = [r for r in read_directory(f, lba, size) if r[0] == part.encode('ascii')]
        if len(matches) != 1:
            raise ValueError('Expected exactly one ISO path: ' + '/'.join(parts))
        _, lba, size, directory = matches[0]
        if directory != (i < len(parts) - 1):
            raise ValueError('Unexpected path type.')
    return lba * SECTOR, size

def apply(source, exe, make_iso_patch=False, expected_iso_sha=None):
    folder = Path(__file__).resolve().parent
    manifest = json.loads((folder / 'technical-details.json').read_text(encoding='utf-8'))
    source, exe = Path(source).resolve(), Path(exe).resolve()
    output = source.with_name(source.stem + '.desktop-ru-v2.iso')
    iso_patch = source.with_name(source.stem + '.desktop-ru-v2.xdelta')
    if not exe.is_file():
        raise ValueError('Place xdelta3.exe beside this script, or specify --xdelta PATH.')
    if output.exists() or (make_iso_patch and iso_patch.exists()):
        raise ValueError('Output already exists; move the previous output first.')
    print('Checking original ISO SHA-256...', flush=True)
    if sha(source) != (expected_iso_sha or manifest['source_iso_sha256']):
        raise ValueError('ISO SHA-256 mismatch. Use the unmodified English ISO.')
    verified = []
    with tempfile.TemporaryDirectory(prefix='infection-ru-') as td:
        for key, spec in manifest['files'].items():
            with source.open('rb') as f:
                offset, size = find_file(f, spec['iso_path'])
                if size != spec['size'] or offset + size > source.stat().st_size:
                    raise ValueError('Unexpected file extent: ' + key)
                f.seek(offset)
                original = f.read(size)
            if hashlib.sha256(original).hexdigest() != spec['source_sha256']:
                raise ValueError('Original file hash mismatch: ' + key)
            old, new = Path(td) / (key + '.old'), Path(td) / (key + '.new')
            old.write_bytes(original)
            subprocess.run([str(exe), '-D', '-R', '-d', '-s', str(old), str(folder / spec['patch']), str(new)], check=True)
            if new.stat().st_size != size or sha(new) != spec['target_sha256']:
                raise ValueError('Patched file verification failed: ' + key)
            verified.append((offset, size, new, spec['target_sha256']))
        extents = sorted((o, o + s) for o, s, _, _ in verified)
        if any(a[1] > b[0] for a, b in zip(extents, extents[1:])):
            raise ValueError('Overlapping ISO file extents.')
        print('Writing translated ISO copy...', flush=True)
        created = False
        try:
            with source.open('rb') as inp, output.open('xb') as out:
                created = True
                shutil.copyfileobj(inp, out, 8 * 1024 * 1024)
            with output.open('r+b') as f:
                for offset, size, new, digest in verified:
                    f.seek(offset)
                    f.write(new.read_bytes())
            with output.open('rb') as f:
                for offset, size, new, digest in verified:
                    f.seek(offset)
                    if hashlib.sha256(f.read(size)).hexdigest() != digest:
                        raise ValueError('ISO write verification failed.')
            if output.stat().st_size != source.stat().st_size:
                raise ValueError('ISO size changed unexpectedly.')
        except BaseException:
            if created:
                output.unlink(missing_ok=True)
            raise
    print('Created:', output, flush=True)
    if make_iso_patch:
        print('Creating xdelta for the complete original ISO...', flush=True)
        subprocess.run([str(exe), '-e', '-s', str(source), str(output), str(iso_patch)], check=True)
        print('Created:', iso_patch)
    return output

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('iso', type=Path)
    ap.add_argument('--xdelta', type=Path, default=Path(__file__).with_name('xdelta3.exe'))
    ap.add_argument('--make-iso-patch', action='store_true')
    args = ap.parse_args()
    apply(args.iso, args.xdelta, args.make_iso_patch)
    print('Boot the new ISO from scratch in PCSX2. Do not load an old emulator save state.')

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        raise SystemExit('ERROR: ' + str(exc))
