from pathlib import Path
import json,hashlib,shutil,subprocess
R=Path(__file__).resolve().parent.parent;W=R/'desktop_work';O=R/'deliverables/desktop-ru-v1';O.mkdir(exist_ok=True)
hash=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();source=R/'analysis_inputs/infection-analysys';lay=json.loads((W/'build_layout.json').read_text());prev=json.loads((R/'deliverables/dialogues-ru-v1/technical-details.json').read_text());specs={
'main':(source/'SLUS_202.67',W/'SLUS_202.67.desktop-ru-v1',['SLUS_202.67']),
'gcmn':(source/'DATA/GCMN.PRG',R/'translation_work/GCMN.PRG.dialogues-ru-v1',['DATA','GCMN.PRG']),
'desktop':(source/'DATA/DESKTOP.PRG',W/'DESKTOP.PRG.desktop-ru-v1',['DATA','DESKTOP.PRG']),
'toppage':(source/'DATA/TOPPAGE.PRG',W/'TOPPAGE.PRG.desktop-ru-v1',['DATA','TOPPAGE.PRG']),
'data':(R/'upload/DATA.BIN',W/'DATA.BIN.desktop-ru-v1',['DATA','DATA.BIN'])}
manifest={'source_iso_sha256':prev['source_iso_sha256'],'files':{},'font_base':'cyrillic-v3','segment_file_bytes':lay['segment_bytes'],'heap_start':lay['heap_start'],'mail_records':326,'reply_records':294,'bbs_records':341,'threads':63,'news_pages':69,'news_pages_retypeset':68,'corrupted_news_preserved':1,'dialogue_descriptors':2304,'scope':'Cumulative dialogue, font, mail, replies, BBS and news patch. Item descriptions and general UI remain outside scope. Includes source-resident records which may be unused in Part 1.'}
for key,(old,new,iso) in specs.items():
 assert old.stat().st_size==new.stat().st_size
 patch=key+'-ru.xdelta';subprocess.run([str(R/'tool_src/xdelta3'),'-f','-D','-R','-e','-s',str(old),str(new),str(O/patch)],check=True)
 out=W/(key+'.roundtrip');subprocess.run([str(R/'tool_src/xdelta3'),'-f','-D','-R','-d','-s',str(old),str(O/patch),str(out)],check=True);assert hash(out)==hash(new)
 manifest['files'][key]={'iso_path':iso,'source_sha256':hash(old),'target_sha256':hash(new),'size':new.stat().st_size,'patch':patch};print(key,'patch', (O/patch).stat().st_size,'roundtrip PASS',flush=True)
(O/'technical-details.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));s=(R/'deliverables/dialogues-ru-v1/apply_iso.py').read_text().replace('.dialogues-ru-v1','.desktop-ru-v1').replace("[str(exe), '-d', '-s'","[str(exe), '-D', '-R', '-d', '-s'");(O/'apply_iso.py').write_text(s)
for name in ['documents_ru.json','threads_ru.json','news_ru.json'] :shutil.copyfile(W/name,O/name)
shutil.copyfile(R/'deliverables/dialogues-ru-v1/glossary.md',O/'glossary.md')
S=O/'source';S.mkdir(exist_ok=True)
for name in ['ru_mail.txt','ru_reply.txt','replies_ru.json','ru_bbs.txt','ru_threads.txt','ru_news.txt','build_desktop.py','render_news.py','test_runtime.py','catalog.json','news_decoded.json','reuse_replies.py','extract.py','decode_news.py'] :shutil.copyfile(W/name,S/name)
(O/'README.txt').write_text('''.hack//Infection Part 1 NTSC SLUS-20267 — RU desktop v1

Общий патч: прежние диалоги и кириллица v3 + почта, новости и форум.
Накладывайте НА ЧИСТЫЙ АНГЛИЙСКИЙ ISO, а не поверх предыдущего патча.

СОДЕРЖАНИЕ
326 записей входящей почты, 294 варианта ответа игрока,
341 сообщение форума и 63 заголовка веток.
69 новостных страниц: 68 переведены и заново набраны;
одна намеренно испорченная страница оставлена испорченной.
Искажённые письма Ауры также сохранены: это часть повествования.
Включены прежние 2304 записи диалогов и рабочий шрифт v3.
Часть записей в исходных файлах может не использоваться в Part 1.
Общие меню и описания предметов пока не входят в перевод.
Английские названия предметов, областей и пунктов меню в тексте
сохранены для совпадения с интерфейсом.

ПРИМЕНЕНИЕ В WINDOWS
1. Распакуйте архив в отдельную папку.
2. Положите в неё xdelta3.exe (он не включён).
3. Откройте PowerShell в этой папке. Нужен установленный Python 3.
4. Выполните:

py -3 .\\apply_iso.py "C:\\games\\dot Hack 1 (Infection) By Ghaleon\\dot Hack 1 (Infection) By Ghaleon.iso" --make-iso-patch

Скрипт проверит SHA-256 образа, применит пять файловых xdelta-патчей,
создаст рядом копию *.desktop-ru-v1.iso и, благодаря ключу
--make-iso-patch, отдельный xdelta-патч для целого исходного ISO.
Исходный ISO не изменяется. Свободного места нужно на копию ISO
и временные файлы. Файлы *.xdelta из архива — части комплекта;
по отдельности к целому ISO их применять нельзя.

LINUX
python3 apply_iso.py "/путь/к/исходному.iso" --xdelta /путь/к/xdelta3 --make-iso-patch

ЭМУЛЯТОР
Запустите новый ISO в PCSX2 с полной загрузки игры.
Сохранения с карты памяти подходят. Старые состояния эмулятора
(save states) могут содержать старые ресурсы: не загружайте их.

ПРОВЕРКА
Проверены пересборка ресурсов, целостность gzip, размещение текста,
контрольные коды, работа выбранных функций движка в CPU-эмуляции,
обратное применение всех xdelta и сборка тестового ISO.
Полного прохождения в PCSX2 здесь не было. Это первая тестовая сборка.
Проверьте чтение и прокрутку писем, выбор ответов, длинные темы форума,
рейтинг Героев Цайт и открытие новостей.

Ожидаемый SHA-256 исходного ISO:
86f59b3e30012f8b4650c1dc891af9e3aec1663df49120b7eb00c5ebc2672faf

Для редакторской сверки: translation-review.md и *_ru.json.
Технические данные: technical-details.json и validation.json.
''')
(O/'editorial-notes.md').write_text('''# Примечания к переводу

Перевод близок к исходному тексту, с сохранением интонаций и шуток.
Цитируемые ответы сопоставлялись с ответами игрока. Имена основных
персонажей согласованы с предыдущим переводом; Рэйчел — женщина.
Нукэ Усагимару и Рёко Тэраджима переданы по согласованному принципу.

Почта и форум переведены с английских таблиц. В новостных ресурсах
11 страниц содержат английский текст, 57 — японский; ещё одна страница
намеренно испорчена. Японские статьи переведены по изображениям.
Английские заголовки некоторых таких страниц расходятся с картинкой:
например, "яблоки" против мацутакэ, "снежный человек" против цутиноко.
Для этих страниц русский заголовок следует содержанию картинки.
Часть этих ресурсов может быть неиспользуемым остатком локализации;
доступность каждой страницы в игре отдельно не установлена.
Форум при этом сохраняет содержание английских сообщений, поэтому
разночтения между остаточными японскими новостями и английским форумом
могут остаться. Они не исправлялись посредством выдуманного сюжета.

Искажённые письма и новость оставлены исходными. Термины предметов,
ключевых слов и меню оставлены по-английски, если они нужны для поиска
в ещё не переведённом интерфейсе. Имена обычных форумных пользователей
сохранены как никнеймы. Служебные цветовые коды и значки сохранены.

Фотографии и иллюстрации новостей сохранены. Надписи внутри рекламных
картинок, снимков интерфейса и диаграмм в основном остаются исходными;
основной текст статьи и её заголовок переведены. Высота коротких страниц
увеличена там, где это нужно для читаемого русского текста (не более 512).

Прогон в PCSX2 остаётся необходимым для проверки поведения интерфейса,
прокрутки, фактического появления всех событий и визуальной читаемости.
''')
md=['# Почта, форум и новости — редакторская сверка','', 'Коды цветов и подстановки оставлены для контроля. Полные переносы для движка — в documents_ru.json.','']
for d in json.loads((W/'documents_ru.json').read_text()):
 md+=['## '+d['id']+' · '+d['sender'],'','**EN: '+d['title']+'**','','```text',d['source'],'```','','**RU: '+d['translation_title']+'**','','```text',d['source'] if d['translation']=='@KEEP@' else d['translation'].replace('\\|','<PIPE>').replace('|','\n').replace('<PIPE>','|'),'```','']
md+=['# Заголовки веток','']
for t in json.loads((W/'threads_ru.json').read_text()):md+=[t['id']+': '+t['title']+' → '+t['translation'],'']
md+=['# Новости','', 'Для японских исходных страниц английский OCR не является исходным текстом; перевод выполнен по картинке.','']
for k,d in json.loads((W/'news_ru.json').read_text()).items():md+=['## '+k+' · '+d['title'],'',d['body'].replace('||','\n\n').replace('|','\n'),'']
(O/'translation-review.md').write_text('\n'.join(md))
print('Package directory ready',flush=True)
