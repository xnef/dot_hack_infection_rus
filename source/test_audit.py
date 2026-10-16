from pathlib import Path
import json,struct,re,collections
R=Path.cwd();W=R/'fix_logout';ns={};exec((R/'analysis_inputs/test_cyrillic.py').read_text().split('u=create(patched);v=create(original)')[0],ns);globals().update(ns)
b=(W/'main.v1').read_bytes();u=create(b);layout=json.loads((W/'v1/source/build_layout.json').read_text());docs=json.loads((W/'v1/documents_ru.json').read_text());heap=int(layout['heap_start'],16)
def cstr(p):
 out=bytearray()
 while True:
  c=bytes(u.mem_read(p,1));p+=1
  if c==b'\0':return bytes(out)
  out+=c
regions=[]
def guards():
 for p,n in regions:assert bytes(u.mem_read(p+n,32))==b'\xa5'*32,('overrun',hex(p),n)
 regions.clear()
alloc=[0x1300000]
def hook(uc,a,size,data):
 if a==0x1327a8:
  dest=uc.reg_read(UC_MIPS_REG_A0);uc.mem_write(dest,bytes([uc.reg_read(UC_MIPS_REG_A1)&255])*uc.reg_read(UC_MIPS_REG_A2));uc.reg_write(UC_MIPS_REG_V0,dest);uc.reg_write(UC_MIPS_REG_PC,uc.reg_read(UC_MIPS_REG_RA))
 elif a==0x134660:
  uc.reg_write(UC_MIPS_REG_V0,len(cstr(uc.reg_read(UC_MIPS_REG_A0))));uc.reg_write(UC_MIPS_REG_PC,uc.reg_read(UC_MIPS_REG_RA))
 elif a==0x134270:
  p=uc.reg_read(UC_MIPS_REG_A0);n=uc.reg_read(UC_MIPS_REG_A1)&255;raw=cstr(p)+b'\0';at=raw.find(bytes([n]));uc.reg_write(UC_MIPS_REG_V0,p+at if at>=0 else 0);uc.reg_write(UC_MIPS_REG_PC,uc.reg_read(UC_MIPS_REG_RA))
 elif a==0x134548:
  dest=uc.reg_read(UC_MIPS_REG_A0);raw=cstr(uc.reg_read(UC_MIPS_REG_A1));uc.mem_write(dest,raw+b'\0');uc.reg_write(UC_MIPS_REG_V0,dest);uc.reg_write(UC_MIPS_REG_PC,uc.reg_read(UC_MIPS_REG_RA))
 elif a==0x10ba40:
  p=alloc[0];n=uc.reg_read(UC_MIPS_REG_A0);regions.append((p,n));uc.mem_write(p+n,b'\xa5'*32);alloc[0]=(p+n+63)&~15;assert alloc[0]<0x1c00000;uc.reg_write(UC_MIPS_REG_V0,p);uc.reg_write(UC_MIPS_REG_PC,uc.reg_read(UC_MIPS_REG_RA))
 elif a==0x10b870:
  uc.reg_write(UC_MIPS_REG_V0,uc.reg_read(UC_MIPS_REG_A0));uc.reg_write(UC_MIPS_REG_PC,uc.reg_read(UC_MIPS_REG_RA))
 elif a==0x119fb4:uc.reg_write(UC_MIPS_REG_S1,0);uc.reg_write(UC_MIPS_REG_PC,a+4)
 elif a==0x119880:uc.reg_write(UC_MIPS_REG_V0,0x1ffe000);uc.reg_write(UC_MIPS_REG_PC,uc.reg_read(UC_MIPS_REG_RA))
u.hook_add(UC_HOOK_CODE,hook)
saved=bytes(u.mem_read(0x730600,layout['segment_bytes']));u.emu_start(0x100008,0x100034,count=4000000);assert bytes(u.mem_read(0x730600,len(saved)))==saved
for n in [4096,0x12340,0x100000]:
 p=run(u,0x119fa0,n);assert p>=heap;u.mem_write(p,b'\xa5'*n)
assert bytes(u.mem_read(0x730600,len(saved)))==saved
print('PASS original startup clear and heap allocation preserve expanded segment',flush=True)
desktop=(W/'desktop.v1').read_bytes();u.mem_write(0x400800,desktop);before=bytes(u.mem_read(0x41dfd0,326*72));run(u,0x461c30)
# Match all reply records as copied by the real generated initializer.
embedded=[]
for i in range(326):
 p=0x41dfd0+i*72
 assert bytes(u.mem_read(p,32))==before[i*72:i*72+32]
 embedded.extend(bytes(u.mem_read(p+j,20)) for j in [32,52])
replies=[bytes(u.mem_read(0x41c8d0+i*20,20)) for i in range(294)]
assert all(x in embedded for x in replies)
print('PASS real mail initializer copies all 294 translated reply records',flush=True)
checks=0;rasters=0
for doc in docs:
 kind=doc['id'].split(':')[0]
 if kind=='bbs':continue
 guards();alloc[0]=0x1300000;obj=0x1200000;u.mem_write(obj,b'\0'*0x200);u.mem_write(obj+0xe0,struct.pack('<I',0xffffffff))
 run(u,0x409b60 if kind=='mail' else 0x409e20,obj,int(doc['table_va'],16))
 pp=struct.unpack('<I',u.mem_read(obj+(0x10c if kind=='mail' else 0x110),4))[0]
 for i,line in enumerate(doc['lines']):
  p=struct.unpack('<I',u.mem_read(pp+4*i,4))[0];expected=re.sub(rb'\{([0-9A-Fa-f]{4})\}',lambda m:bytes.fromhex(m[1].decode()),line.encode('cp1251'));assert cstr(p)==expected,(doc['id'],i)
  checks+=1
print('PASS mail and reply line pointer construction:',checks,'lines',flush=True)
u.mem_write(0x400800,(W/'toppage.v2').read_bytes());bbschecks=0
for doc in docs:
 if not doc['id'].startswith('bbs:'):continue
 guards();alloc[0]=0x1300000;obj=0x1200000;u.mem_write(obj,b'\0'*0x500);u.mem_write(0x1210000,struct.pack('<I',0));run(u,0x404310,obj,0x1210000,0,int(doc['table_va'],16),0)
 assert bytes(u.mem_read(obj+0x474,4))!=b'\0'*4
 for i,line in enumerate(doc['lines']):
  p=struct.unpack('<I',u.mem_read(obj+0x280+4*i,4))[0];expected=re.sub(rb'\{([0-9A-Fa-f]{4})\}',lambda m:bytes.fromhex(m[1].decode()),line.encode('cp1251'));assert cstr(p)==expected,(doc['id'],i)
  assert run(u,0x404720,obj,i)==p
  if line:assert run(u,0x404610,obj,i)>0
  bbschecks+=1
print('PASS BBS object initialization and line access:',bbschecks,'lines',flush=True)
# Test dynamic ranking separately with synthetic game save data.
guards();doc=next(d for d in docs if d['id']=='bbs:186');alloc[0]=0x1300000;obj=0x1200000;u.mem_write(obj,b'\0'*0x500);u.mem_write(0x1210000,struct.pack('<I',29));u.mem_write(0x37faf0-0x7118,struct.pack('<I',0x1220000))
for i in range(5):
 u.mem_write(0x1220000+i*40+0x6789,b'00:01:23\0');u.mem_write(0x1220000+i*40+0x6775,b'ABCDEFGHIJKLMNOPQRS\0')
run(u,0x404310,obj,0x1210000,1,int(doc['table_va'],16),0)
for j in [7,12,17,22,27]:
 p=struct.unpack('<I',u.mem_read(obj+0x274+4*j,4))[0];q=struct.unpack('<I',u.mem_read(obj+0x274+4*(j+1),4))[0];assert cstr(p)=='#WВремя: 00:01:23'.encode('cp1251');assert cstr(q)=='Игрок: ABCDEFGHIJKLMNOPQRS'.encode('cp1251')
print('PASS dynamic ranking times/names and Russian prefixes',flush=True)
guards();print('PASS allocation guards: mail, replies, BBS, ranking',flush=True)
# Raster and real proportional font width checks across every authored body line.
linecount=0
for doc in docs:
 if doc['translation']=='@KEEP@':continue
 for i,line in enumerate(doc['lines']):
  clean=re.sub(r'#[WYBGR]','',line);clean=clean.replace('#0','Ш'*8);raw=re.sub(rb'\{([0-9A-Fa-f]{4})\}',lambda m:bytes.fromhex(m[1].decode()),clean.encode('cp1251'))
  if not raw:continue
  text(u,raw);actual=run(u,0x15f2a0,0x10000,1);assert actual<= (400 if doc['id'].startswith('bbs:') else 272),(doc['id'],i,actual,doc['widths'][i],line)
  if linecount%137==0:
   n,buf=extract(u,raw,1);assert n and any(buf);rasters+=1
  linecount+=1
print('PASS',linecount,'body widths and',rasters,'sample rasters in small Cyrillic font',flush=True)
(W/'runtime_validation.json').write_text(json.dumps({'startup_and_heap':'pass','reply_initializer':294,'mail_reply_lines':checks,'bbs_lines':bbschecks,'dynamic_ranking':'pass','body_widths':linecount,'sample_rasters':rasters,'full_pcsx2':'unavailable; gameplay verification pending'},indent=2))
