"""Repair a desktop-ru-v1 ISO by creating a corrected copy. No xdelta executable needed."""
import argparse,hashlib,json,shutil
from pathlib import Path
from apply_iso import find_file

def repair(source):
    source=Path(source).resolve()
    output=source.with_name(source.stem+'.logout-fix-v2.iso')
    manifest=json.loads(Path(__file__).with_name('technical-details.json').read_text(encoding='utf-8'))
    if output.exists():raise ValueError('Output already exists: '+str(output))
    verified=[];top=None
    print('Checking all five translated files...',flush=True)
    with source.open('rb') as f:
        for key,spec in manifest['files'].items():
            offset,size=find_file(f,spec['iso_path'])
            if size!=spec['size'] or offset+size>source.stat().st_size:raise ValueError('Invalid file extent: '+key)
            f.seek(offset);data=f.read(size)
            expected=manifest['hotfix']['source_toppage_sha256'] if key=='toppage' else spec['target_sha256']
            if hashlib.sha256(data).hexdigest()!=expected:raise ValueError('Not the supported desktop-ru-v1 build: '+key)
            verified.append((offset,size,spec['target_sha256']))
            if key=='toppage':top=(offset,bytearray(data))
    extents=sorted((o,o+s) for o,s,_ in verified)
    if any(a[1]>b[0] for a,b in zip(extents,extents[1:])):raise ValueError('Overlapping file extents')
    offset,data=top
    for change in manifest['hotfix']['changes']:
        i=change['offset']
        if data[i]!=change['before']:raise ValueError('Unexpected instruction bytes')
        data[i]=change['after']
    if hashlib.sha256(data).hexdigest()!=manifest['files']['toppage']['target_sha256']:raise ValueError('Fix validation failed')
    created=False
    try:
        print('Creating corrected ISO copy...',flush=True)
        with source.open('rb') as inp,output.open('xb') as out:
            created=True;shutil.copyfileobj(inp,out,8*1024*1024)
        with output.open('r+b') as f:f.seek(offset);f.write(data)
        if output.stat().st_size!=source.stat().st_size:raise ValueError('ISO size changed')
        with output.open('rb') as f:
            for offset,size,digest in verified:
                f.seek(offset)
                if hashlib.sha256(f.read(size)).hexdigest()!=digest:raise ValueError('Output validation failed')
    except BaseException:
        if created:output.unlink(missing_ok=True)
        raise
    print('Created:',output)
    print('Cold boot this ISO; load from memory card. Do not resume the hung save state.')
    return output

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('iso',type=Path)
    try:repair(parser.parse_args().iso)
    except Exception as exc:raise SystemExit('ERROR: '+str(exc))
