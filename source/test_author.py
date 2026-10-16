from pathlib import Path
import json,struct,re
ns={};exec(Path('analysis_inputs/test_cyrillic.py').read_text().split('u=create(patched);v=create(original)')[0],ns);globals().update(ns)
docs=json.loads(Path('fix_logout/v1/documents_ru.json').read_text())
def test(version,real=False):
 u=create(Path('fix_logout/main.v1').read_bytes());u.mem_write(0x400800,Path(f'fix_logout/toppage.{version}').read_bytes());alloc=[0x1300000];regions=[]
 def cs(p):
  out=bytearray()
  for _ in range(65536):
   c=bytes(u.mem_read(p,1));p+=1
   if c==b'\0':return bytes(out)
   out+=c
  raise AssertionError('unterminated')
 def hook(uc,a,size,data):
  def ret(v):uc.reg_write(UC_MIPS_REG_V0,v);uc.reg_write(UC_MIPS_REG_PC,uc.reg_read(UC_MIPS_REG_RA))
  x=uc.reg_read(UC_MIPS_REG_A0);y=uc.reg_read(UC_MIPS_REG_A1)
  if a==0x1004e4 and real:uc.reg_write(UC_MIPS_REG_PC,STOP)
  elif a==0x134660:ret(len(cs(x)))
  elif a==0x134548:uc.mem_write(x,cs(y)+b'\0');ret(x)
  elif a==0x134270:
   at=(cs(x)+b'\0').find(bytes([y&255]));ret(x+at if at>=0 else 0)
  elif a==0x1327a8:uc.mem_write(x,bytes([y&255])*uc.reg_read(UC_MIPS_REG_A2));ret(x)
  elif a==0x131a20 and real:ret(0x770000)
  elif a==0x10ba40 and not real:
   p=alloc[0];alloc[0]=(p+x+63)&~15;regions.append((p,x));uc.mem_write(p+x,b'\xa5'*32);ret(p)
 u.hook_add(UC_HOOK_CODE,hook)
 if real:
  u.reg_write(UC_MIPS_REG_V1,0x8000);run(u,0x100394)
 count=0;bad=[]
 for doc in docs:
  if not doc['id'].startswith('bbs:'):continue
  if not real:alloc[0]=0x1300000;regions.clear()
  obj=0x80000;thread=0x81000;u.mem_write(obj,b'\0'*0x500);u.mem_write(thread,b'\0'*4)
  try:run(u,0x404310,obj,thread,0,int(doc['table_va'],16),0)
  except Exception as exc:
   print(version,'real',real,'FAILED',doc['id'],repr(exc));return {'count':count,'failure':doc['id'],'error':repr(exc)}
  ap=struct.unpack('<I',u.mem_read(obj+0x474,4))[0]
  for p,n in regions:
   if bytes(u.mem_read(p+n,32))!=b'\xa5'*32:bad.append(doc['id'])
  if version=='v2':assert cs(ap).startswith('Автор: '.encode('cp1251'))
  for i,line in enumerate(doc['lines']):
   p=struct.unpack('<I',u.mem_read(obj+0x280+4*i,4))[0];want=re.sub(rb'\{([0-9A-Fa-f]{4})\}',lambda m:bytes.fromhex(m[1].decode()),line.encode('cp1251'));assert cs(p)==want,(doc['id'],i)
  count+=1
 print(version,'real',real,'count',count,'overruns',len(bad),flush=True)
 return {'count':count,'overruns':len(bad)}
results={}
for real in [False]:
 for version in ['v1','v2']:results[f'{version}_real_{real}']=test(version,real)
Path('fix_logout/author_validation.json').write_text(json.dumps(results,indent=2))
