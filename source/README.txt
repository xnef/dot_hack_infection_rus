Технический снимок проекта для дальнейшей работы.

Для применения перевода эти файлы не нужны: используйте apply_iso.py
в корне архива. Для самостоятельной пересборки нужен отдельный рабочий
каталог и исходные файлы, которых в архиве нет:

analysis_inputs/infection-analysys/SLUS_202.67
analysis_inputs/infection-analysys/DATA/DESKTOP.PRG
analysis_inputs/infection-analysys/DATA/TOPPAGE.PRG
analysis_inputs/infection-analysys/DATA/GCMN.PRG
analysis_inputs/data_inventory.json (индекс gzip исходного DATA.BIN)
upload/DATA.BIN
translation_work/SLUS_202.67.dialogues-ru-v1
translation_work/GCMN.PRG.dialogues-ru-v1
deliverables/dialogues-ru-v1/technical-details.json
analysis_inputs/test_cyrillic.py (CPU harness предыдущего этапа)
tool_src/xdelta3

Исходники этого архива следует разместить в desktop_work/ такого
каталога. Предыдущие целевые файлы восстанавливаются из оригиналов
патчами предыдущей сборки infection-dialogues-ru-v1.zip.

Порядок: decode_news.py, render_news.py, build_desktop.py,
package_patch.py; затем CPU/ISO проверки. catalog.json и *_ru.json
уже содержат используемые переводы. replies_ru.json — итог всех
294 ответов; ru_reply.txt — только ручные дополнения к автосверке.
ru_news.txt содержит перевод статей, а не результат английского OCR.

Сборочные зависимости: Python, Pillow, NumPy, SciPy, DejaVu Sans,
xdelta3. Для извлечения OCR — tesseract. Для CPU-проверок — Unicorn.
В CPU harness стандартные libc-операции, выделение памяти и
конструктор массива заменены семантическими заглушками; код игры,
инициализатор ответов, разбор строк и функции шрифта исполняются.
Полная работа GPU и PCSX2 этим не проверяется.
