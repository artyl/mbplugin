%~d0 
cd "%~dp0"

@REM ��� ��� �������� ������������ python ��� __pycache__
set PYTHONDONTWRITEBYTECODE=x

@REM ������� � ����������� � mbplugin\python:https://www.python.org/ftp/python/3.8.3/python-3.8.3-embed-win32.zip
if not exist python38.zip curl -LOk https://www.python.org/ftp/python/3.8.3/python-3.8.3-embed-win32.zip
if not exist python38.zip 7z x python-3.8.3-embed-win32.zip
if exist python-3.8.3-embed-win32.zip del python-3.8.3-embed-win32.zip

@REM ������� https://bootstrap.pypa.io/get-pip.py � mbplugin\python
if not exist get-pip.py   curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py

@REM �������� � ����� mbplugin\python ��������� 
if not exist Scripts\pip.exe python get-pip.py

@REM � ����� mbplugin\python\python38._pth ���������������� (������ #) import site
..\python\python -c "d=open('python38._pth').read();open('python38._pth','w').write(d.replace('#import site','import site'))"

@REM ��������� � sys.path ����� � ����� ������ ������� ������ �� ���������, � embedded �� ������-�� ��������
..\python\python -c "txt='''import os,sys\nsys.path.insert(0,os.path.split(sys.argv[0])[0])''';open('sitecustomize.py','w').write(txt)"

@REM �������� mbplugin\python ��������� 
..\python\python -m pip install --upgrade python-telegram-bot requests pillow beautifulsoup4 pyodbc pyreadline pywin32 pyppeteer psutil pystray playwright schedule

@REM � ��������� �� ����� ��������� ���������� �� ��������� tkinter ������ ���������� �� �������������� python
@rem https://stackoverflow.com/questions/37710205/python-embeddable-zip-install-tkinter


