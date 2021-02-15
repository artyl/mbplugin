# -*- coding: utf8 -*-
''' Получение иконки с сайта в виде строки для вставки в jsmb plugin
иконка на сайте может быть в виде http://examples.com/favicon.ico
либо на странице сайта в тексте html в теге link c rel="apple-touch-icon":
<link rel="apple-touch-icon" sizes="48x48" href="/fav@3x.png">
запуск:
get_icon.py путь_к_иконке
например:
get_icon.py https://vscale.io/fav.png
или
get_icon.py https://my.mosenergosbyt.ru/favicon.ico
или 
get_icon.py имя_файла_на_диске.ico
'''
import zlib,requests,io,sys,os
from PIL import Image
if os.path.exists(sys.argv[1]):
    img = Image.open(sys.argv[1])
else:
    bb = io.BytesIO(requests.get(sys.argv[1]).content)
    img = Image.open(bb)
img = img.resize((16,16))
bb=io.BytesIO()
img.save(bb, 'bmp')
bb.getvalue()
print(zlib.compress(bb.getvalue()).hex())
