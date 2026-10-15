from pathlib import Path
import json,zlib,struct,subprocess
from PIL import Image
R=Path('/workspace/scratch/b3fb308928df');cat=json.loads((R/'desktop_work/catalog.json').read_text());inventory=json.loads((R/'analysis_inputs/data_inventory.json').read_text());src=(R/'upload/DATA.BIN').read_bytes();out=R/'desktop_work/news';out.mkdir(exist_ok=True)
for n in cat['news']:
 if not n['height']:continue
 a=next(x for x in inventory if x['name']==n['asset']+'.cmp');d=zlib.decompress(src[a['offset']:a['offset']+a['compressed_bytes']],31);pal=d.find(b'\x00\x04\xcc\xcc');tex=d.find(b'\x00\x03\xcc\xcc');assert pal>=0 and tex>=0
 w,h=1<<d[tex+24],1<<d[tex+25];p=d[pal+28:pal+28+1024];start=tex+36;idx=d[start:start+w*h];assert len(idx)==w*h
 im=Image.frombytes('P',(w,h),idx);im.putpalette(bytes(v for i in range(256) for v in p[i*4:i*4+3]));im=im.convert('RGB').transpose(Image.Transpose.FLIP_TOP_BOTTOM);im.save(out/(n['asset']+'.png'))
 (out/(n['asset']+'.ccs')).write_bytes(d);n.update({'width':w,'texture_height':h,'pixel_offset':start,'palette_offset':pal+28,'member_offset':a['offset'],'member_compressed_bytes':a['compressed_bytes']})
 cp=out/(n['asset']+'-ocr.png');im.crop((0,0,360,min(h,n['height']))).resize((720,min(h,n['height'])*2)).save(cp)
 cached=out/(n['asset']+'.txt')
 if cached.exists():raw=cached.read_text()
 else:raw=subprocess.run(['tesseract',str(cp),'stdout','--psm','3'],capture_output=True,text=True,check=True).stdout;cached.write_text(raw)
 n['ocr_source']=raw
 print(n['id'],n['asset'],w,h,'OCR chars',len(raw),flush=True)
(R/'desktop_work/news_decoded.json').write_text(json.dumps([n for n in cat['news'] if n['height']],ensure_ascii=False,indent=2))
