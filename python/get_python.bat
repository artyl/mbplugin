%~d0 
cd "%~dp0"

@REM �� ��� ᮧ����� ����ਡ�⨢� python ��� __pycache__
set PYTHONDONTWRITEBYTECODE=x

@REM ������ � �ᯠ������ � mbplugin\python:https://www.python.org/ftp/python/3.8.3/python-3.8.3-embed-win32.zip
if not exist python38.zip curl -LOks https://www.python.org/ftp/python/3.8.3/python-3.8.3-embed-win32.zip
if not exist python38.zip 7z x python-3.8.3-embed-win32.zip
if exist python-3.8.3-embed-win32.zip del python-3.8.3-embed-win32.zip

@ECHO Install package
@REM ������ https://bootstrap.pypa.io/get-pip.py � mbplugin\python
if not exist get-pip.py   curl -s https://bootstrap.pypa.io/get-pip.py -o get-pip.py

@REM ��室��� � ����� mbplugin\python �믮����� 
if not exist Lib\site-packages\pip python get-pip.py -q --no-warn-script-location 

@REM � 䠩�� mbplugin\python\python38._pth �᪮����஢��� (���� #) import site
..\python\python -c "d=open('python38._pth').read();open('python38._pth','w').write(d.replace('#import site','import site'))"

@REM ������塞 � sys.path ���� � ����� ��㤠 ����饭 �ਯ� �� 㬮�砭��, � embedded �� ��祬�-� �몫�祭
..\python\python -c "txt='''import os,sys\nsys.path.insert(0,os.path.abspath(os.path.split(sys.argv[0])[0]))''';open('sitecustomize.py','w').write(txt)"

@REM ��室��� mbplugin\python �믮����� 
@REM ..\python\python -m pip install --upgrade python-telegram-bot requests pillow beautifulsoup4 pyodbc pyreadline pywin32 psutil pystray playwright schedule click cryptography
@REM ..\python\python -m pip freeze >..\docker\requirements_win.txt
..\python\python -m pip install -q --no-warn-script-location -r ..\docker\requirements_win.txt

@REM � ᮦ������ �� ��襫 ����塞�� ������樨 �� ��⠭���� tkinter ⮫쪮 ��५����� �� ��⠭��������� python
@REM �������� ⥬� � tkinter ����� ���� �� ����⥫�, ⠪ �� �� �����騩 ������ �� �ᮡ���� �� � �ਭ樯� � �㦥�
@rem https://stackoverflow.com/questions/37710205/python-embeddable-zip-install-tkinter


