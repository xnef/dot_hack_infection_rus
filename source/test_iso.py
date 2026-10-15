from pathlib import Path
import struct,json,hashlib,importlib.util,subprocess
R=Path(__file__).resolve().parent.parent;W=R/'desktop_work';O=R/'deliverables/desktop-ru-v1';F=W/'iso_fixture';F.mkdir(exist_ok=True);S=2048
manifest=json.loads((O/'technical-details.json').read_text());orig={'main':R/'analysis_inputs/infection-analysys/SLUS_202.67','gcmn':R/'analysis_inputs/infection-analysys/DATA/GCMN.PRG','desktop':R/'analysis_inputs/infection-analysys/DATA/DESKTOP.PRG','toppage':R/'analysis_inputs/infection-analysys/DATA/TOPPAGE.PRG','data':R/'upload/DATA.BIN'}
lba=22;ext={}
for k,p in orig.items():ext[k]=(lba,p.stat().st_size);lba+=(p.stat().st_size+S-1)//S
b=bytearray((lba+1)*S)
def rec(name,lba,size,directory=False):
 n=len(name);r=bytearray(33+n+(n%2==0));r[0]=len(r);struct.pack_into('<I',r,2,lba);struct.pack_into('>I',r,6,lba);struct.pack_into('<I',r,10,size);struct.pack_into('>I',r,14,size);r[25]=2 if directory else 0;struct.pack_into('<H',r,28,1);struct.pack_into('>H',r,30,1);r[32]=n;r[33:33+n]=name;return r
pvd=memoryview(b)[16*S:17*S];pvd[:7]=b'\1CD001\1';struct.pack_into('<H',pvd,128,S);struct.pack_into('>H',pvd,130,S);rr=rec(b'\0',20,S,True);pvd[156:156+len(rr)]=rr
root=rec(b'\0',20,S,True)+rec(b'\1',20,S,True)+rec(b'SLUS_202.67;1',*ext['main'])+rec(b'DATA',21,S,True);b[20*S:20*S+len(root)]=root
data=rec(b'\0',21,S,True)+rec(b'\1',20,S,True)
for k in ['gcmn','desktop','toppage','data']:data+=rec((manifest['files'][k]['iso_path'][-1]+';1').encode(),*ext[k])
b[21*S:21*S+len(data)]=data
for k,p in orig.items():start,size=ext[k];b[start*S:start*S+size]=p.read_bytes()
source=F/'synthetic.iso';source.write_bytes(b);output=F/'synthetic.desktop-ru-v1.iso';delta=F/'synthetic.desktop-ru-v1.xdelta';output.unlink(missing_ok=True);delta.unlink(missing_ok=True)
spec=importlib.util.spec_from_file_location('apply_iso',O/'apply_iso.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
# Hash rejection is tested before any output exists.
try:m.apply(source,R/'tool_src/xdelta3')
except ValueError as e:assert 'mismatch' in str(e)
else:raise AssertionError('must reject wrong ISO')
out=m.apply(source,R/'tool_src/xdelta3',True,hashlib.sha256(b).hexdigest());assert source.read_bytes()==b;assert out.stat().st_size==len(b)
with out.open('rb') as f:
 end=0
 for k,(lba,size) in ext.items():
  f.seek(end);assert f.read(lba*S-end)==b[end:lba*S];f.seek(lba*S);assert hashlib.sha256(f.read(size)).hexdigest()==manifest['files'][k]['target_sha256'];end=lba*S+size
 f.seek(end);assert f.read()==b[end:]
try:m.apply(source,R/'tool_src/xdelta3',expected_iso_sha=hashlib.sha256(b).hexdigest())
except ValueError as e:assert 'exists' in str(e)
else:raise AssertionError('must reject overwrite')
roundtrip=F/'roundtrip.iso';subprocess.run([str(R/'tool_src/xdelta3'),'-f','-D','-R','-d','-s',str(source),str(delta),str(roundtrip)],check=True);assert m.sha(roundtrip)==m.sha(output)
(W/'iso_validation.json').write_text(json.dumps({'fixture_files':5,'apply':'pass','unrelated_bytes':'unchanged','original':'unchanged','size':'unchanged','wrong_sha256':'rejected','existing_output':'rejected','whole_iso_xdelta_roundtrip':'pass','real_full_iso_available':False},indent=2));print('PASS five-file ISO application, safeguards, unrelated bytes, and complete-ISO xdelta roundtrip',flush=True)
