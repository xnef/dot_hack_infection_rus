from pathlib import Path
import json,struct,re
R=Path('/workspace/scratch/b3fb308928df');base=0x400800
files={k:(R/('analysis_inputs/infection-analysys/DATA/'+k+'.PRG')).read_bytes() for k in ['DESKTOP','TOPPAGE']}
def text(b,p,count=1):
 f=p-base;ls=[]
 for _ in range(count):
  e=b.find(b'\0',f);assert e>=f;ls.append(b[f:e]);f=e+1
 return ls

def display(b):
 s='';i=0
 while i<len(b):
  if b[i] in (0x81,0x83) and i+1<len(b):s+='{'+b[i:i+2].hex().upper()+'}';i+=2
  else:s+=chr(b[i]);i+=1
 return s
rows=[];b=files['DESKTOP']
for kind,va,n,stride in [('mail',0x41dfd0,326,72),('reply',0x41c8d0,294,20)]:
 for i in range(n):
  a=va+i*stride;w=struct.unpack_from('<'+str(stride//4)+'I',b,a-base);tp,sp,lp,ct=(w[3],w[4],w[7],w[6]) if kind=='mail' else (w[1],w[2],w[4],w[3]);assert 0<ct<300
  ls=text(b,lp,ct);title=display(text(b,tp)[0]);sender=display(text(b,sp)[0]);body='\n'.join(map(display,ls));rows.append({'id':kind+':'+str(i),'file':'DESKTOP','table_va':hex(a),'title':title,'sender':sender,'source':body,'line_count':ct,'pointers':{'title':hex(tp),'sender':hex(sp),'body':hex(lp)},'words':list(w)})
b=files['TOPPAGE']
for i in range(341):
 a=0x4049a0+i*20;w=struct.unpack_from('<5I',b,a-base);ct,tp,sp,lc,bp=w;assert 0<lc<300
 rows.append({'id':'bbs:'+str(i),'file':'TOPPAGE','table_va':hex(a),'title':display(text(b,tp)[0]),'sender':display(text(b,sp)[0]),'source':'\n'.join(map(display,text(b,bp,lc))),'line_count':lc,'pointers':{'title':hex(tp),'sender':hex(sp),'body':hex(bp)},'words':list(w)})
threads=[]
for i in range(63):
 a=0x406450+i*12;tp,msg,n=struct.unpack_from('<III',b,a-base);threads.append({'id':'thread:'+str(i),'table_va':hex(a),'title':display(text(b,tp)[0]),'start':(msg-0x4049a0)//20,'count':n,'title_va':hex(tp)})
news=[];b=files['DESKTOP']
for i in range(70):
 a=0x41c120+i*28;w=struct.unpack_from('<7I',b,a-base);news.append({'id':'news:'+str(i),'table_va':hex(a),'title':display(text(b,w[2])[0]),'asset':display(text(b,w[3])[0]),'texture':display(text(b,w[4])[0]),'height':w[6],'words':list(w)})
(R/'desktop_work/catalog.json').write_text(json.dumps({'documents':rows,'threads':threads,'news':news},ensure_ascii=False,indent=2))
for kind in ['mail','reply','bbs']:
 rr=[r for r in rows if r['id'].startswith(kind+':')];print(kind,len(rr),'chars',sum(len(r['source']) for r in rr),'words',sum(len(r['source'].split()) for r in rr))
 out=[]
 for r in rr:out+=['\n### '+r['id']+' | '+r['sender']+' | '+r['title'],r['source'].replace('\n',' / ')]
 (R/('desktop_work/source_'+kind+'.txt')).write_text('\n'.join(out))
print('threads',len(threads),'news',len(news));print(news[:3])
