from pathlib import Path
import json,struct,re,collections,hashlib
R=Path(__file__).resolve().parent.parent;W=R/'desktop_work';BASE=0x730600;FILE=0x35ab00;OV=0x400800
cat=json.loads((W/'catalog.json').read_text());prev=json.loads((R/'deliverables/dialogues-ru-v1/technical-details.json').read_text());main=bytearray((R/'translation_work/SLUS_202.67.dialogues-ru-v1').read_bytes());files={k:bytearray((R/f'analysis_inputs/infection-analysys/DATA/{k}.PRG').read_bytes()) for k in ['DESKTOP','TOPPAGE']};pool=bytearray(main[FILE:FILE+prev['segment_file_bytes']]);trim=struct.unpack_from('<224h',main,FILE+0x73a980-BASE)
def normalize(s):return s.replace('—','-').replace('–','-').replace('«','"').replace('»','"').replace('…','...').replace('\r','')
def encode(s):
 b=re.sub(rb'\{([0-9A-Fa-f]{4})\}',lambda m:bytes.fromhex(m[1].decode()),normalize(s).encode('cp1251'))
 i=0
 while i<len(b):
  c=b[i]
  if c in [0x81,0x83]:i+=2;continue
  assert c==0 or c==10 or 32<=c<128 or c in [0xa8,0xb8] or c>=0xc0,(s,hex(c))
  i+=1
 return b
def width(s):
 b=encode(s);i=0;v=0
 while i<len(b):
  c=b[i]
  if c==35 and i+1<len(b):
   n=b[i+1];v+=64 if n==48 else (8 if 49<=n<=57 else 0);i+=2;continue
  if c in [0x81,0x83]:v+=8;i+=2;continue
  if c:v+=max(8,8-trim[c-32])
  i+=1
 return v
def wrap(s,limit):
 if not s:return ['']
 lines=[];line='';color=''
 for word in s.split():
  candidate=(line+' '+word).strip()
  if width(candidate)>limit and line:
   active=re.findall(r'#([YBGRW])',line)
   if active:color=active[-1]
   lines.append(line+('#W' if color not in ['','W'] else ''));line=('#'+color if color not in ['','W'] else '')+word
  else:line=candidate
  assert width(line)<=limit,('word too long',line,width(line),limit)
 lines.append(line);return lines

def layout(body,source,kind,ident):
 if body=='@KEEP@':return source.split('\n')
 pieces=re.split(r'(?<!\\)\|',normalize(body).replace('\n','|'));lines=[]
 for p in pieces:lines.extend(wrap(p.replace('\\|','|'),272 if kind!='bbs' else 400))
 if source.startswith('\n') and (not lines or lines[0]):lines.insert(0,'')
 if source.endswith('\n') and lines[-1]:lines.append('')
 if ident=='bbs:186':
  assert len(lines)==27,(ident,len(lines));assert all(lines[j].startswith('Время:') for j in [4,9,14,19,24])
 assert kind!='bbs' or len(lines)<=125,(ident,'BBS pointer array overflow',len(lines))
 return lines

def rows(path):
 out={}
 for line in path.read_text().splitlines():
  if not line.strip():continue
  ident,title,body=line.split('|',2);assert ident not in out;out[ident]={'title':title,'body':body}
 return out
ru={**rows(W/'ru_mail.txt'),**rows(W/'ru_bbs.txt'),**json.loads((W/'replies_ru.json').read_text())};assert len(ru)==961
names={'Orca':'Орка','BlackRose':'БлэкРоуз','Mia':'Мия','Elk':'Элк','Mistral':'Мистраль','Piros':'Пирос','Balmung':'Балмунг','Helba':'Хельба','Lios':'Лиос','Gardenia':'Гардения','Natsume':'Нацумэ','Sanjuro':'Санджуро','Aura':'Аура','Wiseman':'Вайзман','Nuke Usagimaru':'Нукэ Усагимару','Rachel':'Рэйчел','Terajima Ryoko':'Рёко Тэраджима','Deleted':'Удалено','Admin of Time':'Хранитель времени','Administrator':'Администратор'}
cache={}
def add(raw):
 if raw in cache:return cache[raw]
 p=BASE+len(pool);pool.extend(raw);cache[raw]=p;return p
def string(s):return add(encode(s)+b'\0')
def put(file,va,word,val):struct.pack_into('<I',files[file],va-OV+word*4,val)
issues=[];out=[]
ctl=lambda s:collections.Counter(re.findall(r'#[A-Z0-9]|\{[0-9A-Fa-f]{4}\}',s))
for doc in cat['documents']:
 ident=doc['id'];kind=ident.split(':')[0];d=ru[ident];title=doc['title'] if d['title']=='@KEEP@' else normalize(d['title']);body=d['body'];file=doc['file'];va=int(doc['table_va'],16)
 if body!='@KEEP@':
  assert ctl(doc['source'])==ctl(body),(ident,ctl(doc['source'])-ctl(body),ctl(body)-ctl(doc['source']))
 if d['title']!='@KEEP@':assert ctl(doc['title'])==ctl(title),(ident,'title controls')
 if d['title']!='@KEEP@' and width(title)>(272 if kind!='bbs' else 400):issues.append((ident,'title',width(title),title))
 lines=layout(body,doc['source'],kind,ident);raw=b'\0'.join(map(encode,lines))+b'\0';bp=add(raw)
 sender=names.get(doc['sender'],doc['sender']);tp=string(title) if d['title']!='@KEEP@' else int(doc['pointers']['title'],16);sp=string(sender) if sender!=doc['sender'] else int(doc['pointers']['sender'],16)
 if kind=='mail':fields={3:tp,4:sp,6:len(lines),7:bp}
 else:fields={1:tp,2:sp,3:len(lines),4:bp}
 for word,value in fields.items():put(file,va,word,value)
 out.append({**doc,'translation_title':title,'translation_sender':sender,'translation':body,'lines':lines,'widths':[width(x) for x in lines],'new_body_va':hex(bp),'new_title_va':hex(tp),'new_sender_va':hex(sp)})
threads={l.split('|',1)[0]:l.split('|',1)[1] for l in (W/'ru_threads.txt').read_text().splitlines()};assert len(threads)==63
for t in cat['threads']:
 s=threads[t['id']];assert ctl(s)==ctl(t['title']);put('TOPPAGE',int(t['table_va'],16),0,string(s));t['translation']=s
news=json.loads((W/'news_ru.json').read_text())
for n in cat['news']:
 if not n['height']:continue
 t=news[n['id']]['title']
 if t!='@KEEP@':put('DESKTOP',int(n['table_va'],16),2,string(t.replace('%','%%')))
# Dynamic ranking prefixes are materialized in small local buffers by the
# original routine. Author strlen and strcpy MUST use the same prefix.
for hi,lo,s in [(0x40454c,0x404550,'#WВремя: '),(0x404560,0x404564,'Игрок: '),(0x404370,0x404374,'Автор: '),(0x404398,0x40439c,'Автор: ')]:
 p=string(s)
 for va,imm in [(hi,(p+0x8000)>>16),(lo,p)]:
  pos=va-OV;v=struct.unpack_from('<I',files['TOPPAGE'],pos)[0];struct.pack_into('<I',files['TOPPAGE'],pos,(v&0xffff0000)|(imm&65535))
# The shared CCS directory stores compressed byte counts. Keep archive offsets
# unchanged and update those counts after news recompression.
news_layout=json.loads((W/'news_layout.json').read_text())
for x in news_layout:
 if x.get('kept_corruption'):continue
 n=next(n for n in cat['news'] if n['id']==x['id']);put('DESKTOP',int(n['table_va'],16),6,x['height']);needle=(n['asset'].upper()+'.CCS').encode();matches=[m.start() for m in re.finditer(re.escape(needle+b'\0'),main)];assert len(matches)==1,matches
 pos=matches[0];archive_off,old,unpacked=struct.unpack_from('<III',main,pos+32);assert old==x['old_compressed'] and unpacked==263500
 assert archive_off+995328==x['member_offset'];struct.pack_into('<I',main,pos+36,x['new_compressed']);x['directory_count_offset']=pos+36
HEAP=(BASE+len(pool)+4095)&~4095
for hi,lo in [(0x10006c,0x100074),(0x100398,0x10039c)]:
 for va,v in [(hi,(HEAP+0x8000)>>16),(lo,HEAP)]:
  pos=va-0xfff00;word=struct.unpack_from('<I',main,pos)[0];struct.pack_into('<I',main,pos,(word&0xffff0000)|(v&65535))
struct.pack_into('<I',main,0x2f77d4-0xfff00,HEAP);main[FILE:FILE+len(pool)]=pool
ph=struct.unpack_from('<I',main,28)[0];struct.pack_into('<8I',main,ph+5*32,1,FILE,BASE,BASE,len(pool),HEAP-BASE,4,128)
sh=struct.unpack_from('<I',main,32)[0];ent,n,ni=struct.unpack_from('<HHH',main,46);sht=[struct.unpack_from('<10I',main,sh+i*ent) for i in range(n)];ns=sht[ni];sn=main[ns[4]:ns[4]+ns[5]]
for i,s in enumerate(sht):
 name=sn[s[0]:].split(b'\0')[0]
 if name==b'.rufnt':struct.pack_into('<I',main,sh+i*ent+20,len(pool))
 elif name==b'heap':struct.pack_into('<I',main,sh+i*ent+12,HEAP)
(W/'SLUS_202.67.desktop-ru-v1').write_bytes(main)
for k,b in files.items():(W/(k+'.PRG.desktop-ru-v1')).write_bytes(b)
(W/'documents_ru.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));(W/'threads_ru.json').write_text(json.dumps(cat['threads'],ensure_ascii=False,indent=2));(W/'text_layout_issues.json').write_text(json.dumps(issues,ensure_ascii=False,indent=2));(W/'build_layout.json').write_text(json.dumps({'heap_start':hex(HEAP),'segment_bytes':len(pool),'news':news_layout},indent=2))
print('documents',len(out),'pool',len(pool),'heap',hex(HEAP),'issues',issues)
