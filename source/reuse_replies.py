from pathlib import Path
import json,re,collections
R=Path('/workspace/scratch/b3fb308928df');c=json.loads((R/'desktop_work/catalog.json').read_text());docs={d['id']:d for d in c['documents']}
ru={}
for row in (R/'desktop_work/ru_mail.txt').read_text().splitlines():
 id,title,body=row.split('|',2);ru[id]={'title':title,'body':body}
def norm(s):return re.sub(r'\s+',' ',s.replace('>','')).strip()
quotes={};titles={}
for id,r in ru.items():
 if r['body']=='@KEEP@':continue
 d=docs[id];sq=[x for x in d['paragraphs'] if x.startswith('>')];rq=[x[1:].strip() for x in r['body'].split('||') if x.startswith('>')]
 if len(sq)==len(rq):
  for s,t in zip(sq,rq):quotes[norm(s)]=t
 if d['title'].startswith('RE:') and r['title'].startswith('Ответ:'):titles[d['title'][3:].strip()]=r['title'][6:].strip()
out={};missing=[]
for d in c['documents']:
 if not d['id'].startswith('reply:'):continue
 body=quotes.get(norm(d['source']));title=titles.get(d['title'])
 out[d['id']]={'title':title,'body':body}
 if not body or not title:missing.append({**d,'auto_title':title,'auto_body':body})
(R/'desktop_work/replies_auto.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));(R/'desktop_work/replies_missing.json').write_text(json.dumps(missing,ensure_ascii=False,indent=2))
print('auto bodies',sum(bool(x['body']) for x in out.values()),'auto titles',sum(bool(x['title']) for x in out.values()))
(R/'desktop_work/replies_missing.txt').write_text('\n'.join(d['id']+' :: '+d['title']+' :: '+d['source'].replace('\n',' / ')+(' [BODY REUSED]' if d['auto_body'] else '')+(' [TITLE REUSED]' if d['auto_title'] else '') for d in missing))
