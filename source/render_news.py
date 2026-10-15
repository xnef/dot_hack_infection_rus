from pathlib import Path
import json, re, io, gzip, zlib
import numpy as np
from scipy import ndimage as nd
from PIL import Image, ImageDraw, ImageFont
R=Path(__file__).resolve().parent.parent;W=R/'desktop_work';N=json.loads((W/'news_decoded.json').read_text());ru={}
for l in (W/'ru_news.txt').read_text().splitlines():
 k,t,b=l.split('|',2);ru[k]={'title':t,'body':b}
assert len(ru)==69
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
inv=json.loads((R/'analysis_inputs/data_inventory.json').read_text());source=(R/'upload/DATA.BIN').read_bytes();target=bytearray(source);results=[]
# Fixed image rectangles, in the unflipped source texture. Advertising artwork
# is kept as artwork; only the surrounding article is typeset again.
overrides={2:[(214,235,326,320),(26,329,169,437),(215,344,326,428)],5:[(183,56,337,184)],6:[(178,133,339,261)],11:[(180,90,325,225)],14:[(9,106,145,249)],17:[(10,54,167,187)],35:[(15,55,147,176)],36:[(20,64,140,226)]}
for a in N:
 k=a['id'];i=int(k.split(':')[1]);p=W/'news'/a['asset'];original=Image.open(str(p)+'.png').convert('RGB');h=a['height'];d=ru[k]
 if d['body']=='@KEEP@':
  results.append({'id':k,'kept_corruption':True});continue
 ar=np.array(original);mask=(ar[:h,:350].min(2)<220);mask[:50]=False
 lab,n=nd.label(mask);boxes=[]
 for label,sl in enumerate(nd.find_objects(lab),1):
  if sl is None:continue
  ys,xs=sl;w=xs.stop-xs.start;hh=ys.stop-ys.start;area=(lab[sl]==label).sum()
  if w>=55 and hh>=35 and area>1600:boxes.append((max(0,xs.start-1),max(50,ys.start-1),min(350,xs.stop+1),min(h,ys.stop+1)))
 boxes=overrides.get(i,boxes)
 # Reject text fragments accidentally connected by a separator line.
 boxes=[b for b in boxes if b[2]-b[0]<240]
 def make(size):
  f=ImageFont.truetype(font,size);lineh=size+3;im=original.copy();dr=ImageDraw.Draw(im);dr.rectangle((0,0,349,511),fill='white')
  # Reuse the source header gradient without its old title.
  ha=np.array(original.crop((12,6,342,39)))
  for row in range(33):
   colors,counts=np.unique(ha[row,18:310],axis=0,return_counts=True);valid=colors.sum(1)>320;colors,counts=colors[valid],counts[valid];ha[row]=colors[counts.argmax()] if len(colors) else ha[max(0,row-1),0]
  header=Image.fromarray(ha);hm=Image.new('L',(330,33));ImageDraw.Draw(hm).rounded_rectangle((0,0,329,32),radius=16,fill=255)
  dr.rounded_rectangle((13,8,343,41),radius=16,fill=(100,100,100));im.paste(header,(12,6),hm)

  title=d['title'];tf=ImageFont.truetype(bold,14)
  while tf.getlength(title)>316 and tf.size>9:tf=ImageFont.truetype(bold,tf.size-1)
  dr.text((177,21),title,font=tf,fill='black',anchor='mm')
  for b in boxes:im.paste(original.crop(b),b[:2])
  y=54;layout=[]
  for para in re.split(r'(?<!\\)\|',d['body']):
   if not para:y+=lineh//2;continue
   words=para.replace('\\|','|').split();j=0
   while j<len(words):
    spans=[(13,338)]
    for x0,y0,x1,y1 in boxes:
     if y+lineh>y0-3 and y<y1+3:
      out=[]
      for l,r in spans:
       if x0>l:out.append((l,min(r,x0-7)))
       if x1<r:out.append((max(l,x1+7),r))
      spans=out
    spans=[s for s in spans if s[1]-s[0]>=65]
    if not spans:y+=lineh;continue
    l,r=max(spans,key=lambda s:s[1]-s[0]);text='';start=j
    while j<len(words) and f.getlength((text+' '+words[j]).strip())<=r-l:
     text=(text+' '+words[j]).strip();j+=1
    if j==start:
     # A long technical word can use the next full-width row.
     if r-l<300:y+=lineh;continue
     raise ValueError((k,words[j],size))
    dr.text((l,y),text,font=f,fill='black',stroke_width=0);layout.append((l,y,r,text));y+=lineh
  return im,y,layout
 for size in [15,14,13,12,11,10]:
  im,end,layout=make(size)
  if end<=507:break
 assert end<=507,(k,h,end)
 newheight=max(h,end+5)
 if newheight<512:ImageDraw.Draw(im).rectangle((0,newheight,349,511),fill='black')
 raw=bytearray(Path(str(p)+'.ccs').read_bytes());po=a['palette_offset'];pal=bytes(v for j in range(256) for v in raw[po+j*4:po+j*4+3]);ref=Image.new('P',(1,1));ref.putpalette(pal)
 indexed=im.quantize(palette=ref,dither=Image.Dither.NONE).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
 start=a['pixel_offset'];raw[start:start+512*512]=indexed.tobytes();assert len(raw)==len(Path(str(p)+'.ccs').read_bytes())
 stream=io.BytesIO()
 with gzip.GzipFile(filename=a['asset']+'.cmp',mode='wb',fileobj=stream,compresslevel=9,mtime=0) as gz:gz.write(raw)
 packed=stream.getvalue();old=a['member_compressed_bytes'];off=a['member_offset'];window=min(x['offset'] for x in inv if x['offset']>off)-off
 assert len(packed)<=window,(k,len(packed),old,window)
 target[off:off+window]=packed+b'\0'*(window-len(packed));assert zlib.decompress(target[off:off+window],31)==raw
 # Save the actual palette-limited preview, not an unrepresentative RGB render.
 preview=indexed.transpose(Image.Transpose.FLIP_TOP_BOTTOM).convert('RGB');preview.save(W/'news'/(a['asset']+'-ru.png'))
 results.append({'id':k,'font_size':size,'body_bottom':end,'height':newheight,'original_height':h,'boxes':boxes,'old_compressed':old,'new_compressed':len(packed),'allocation':window,'needs_size_update':len(packed)>old,'member_offset':off,'layout':layout})
 print(k,size,end,h,len(packed),old,flush=True)
(W/'DATA.BIN.desktop-ru-v1').write_bytes(target);(W/'news_layout.json').write_text(json.dumps(results,ensure_ascii=False,indent=2));(W/'news_ru.json').write_text(json.dumps(ru,ensure_ascii=False,indent=2))
