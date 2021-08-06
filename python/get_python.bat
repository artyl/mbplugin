%~d0 
cd "%~dp0"

@REM это для создания дистрибутива python без __pycache__
set PYTHONDONTWRITEBYTECODE=x

@REM Скачать и распаковать в mbplugin\python:https://www.python.org/ftp/python/3.8.3/python-3.8.3-embed-win32.zip
if not exist python38.zip curl -LOks https://www.python.org/ftp/python/3.8.3/python-3.8.3-embed-win32.zip
if not exist python38.zip 7z x python-3.8.3-embed-win32.zip
if exist python-3.8.3-embed-win32.zip del python-3.8.3-embed-win32.zip

@ECHO Install package
@REM Скачать https://bootstrap.pypa.io/get-pip.py в mbplugin\python
if not exist get-pip.py   curl -s https://bootstrap.pypa.io/get-pip.py -o get-pip.py

@REM Находясь в папке mbplugin\python выполнить 
if not exist Lib\site-packages\pip python get-pip.py -q --no-warn-script-location 

@REM В файле mbplugin\python\python38._pth раскоментировать (убрать #) import site
..\python\python -c "d=open('python38._pth').read();open('python38._pth','w').write(d.replace('#import site','import site'))"

@REM добавляем в sys.path поиск в папке откуда запущен скрипт по умолчанию, в embedded он почему-то выключен
..\python\python -c "txt='''import os,sys\nsys.path.insert(0,os.path.abspath(os.path.split(sys.argv[0])[0]))''';open('sitecustomize.py','w').write(txt)"

@REM Находясь mbplugin\python выполнить 
@REM ..\python\python -m pip install --upgrade python-telegram-bot requests pillow beautifulsoup4 pyodbc pyreadline pywin32 pyppeteer psutil pystray playwright schedule click
@REM ..\python\python -m pip freeze >..\docker\requirements_win.txt
..\python\python -m pip install -q --no-warn-script-location -r ..\docker\requirements_win.txt

@REM К сожалению не нашел вменяемой инструкции по установке tkinter только переложить из установленного python
@REM Вдобавок тема с tkinter нигде пока не полетела, так что на настоящий момент не особенно от в принципе и нужен
@rem https://stackoverflow.com/questions/37710205/python-embeddable-zip-install-tkinter


