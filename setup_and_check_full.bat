@echo OFF
%~d0 
cd "%~dp0\.."
set MBPLUGIN_WRITE_DIAG=YES
if EXIST mbplugin\log\setup_diag.txt del mbplugin\log\setup_diag.txt 

REM ������塞 � sys.path ���� � ����� ��㤠 ����饭 �ਯ� �� 㬮�砭��, � embedded �� ��祬�-� �몫�祭
mbplugin\python\python mbplugin\plugin\util.py fix-embedded-python-path

REM ���⠢�塞 ��६���� �� ���祭�� � mbplugin.ini
if "%1"=="noweb" mbplugin\python\python mbplugin\plugin\util.py set ini/HttpServer/start_http=0

REM �᫨ �ᯮ��㥬 ���஥��� ��㧥� ����᪠�� playwright install chromium
mbplugin\python\python mbplugin\plugin\util.py install-chromium

REM ��頥� ��� ��㧥� (⮫쪮 � full)
mbplugin\python\python mbplugin\plugin\util.py clear-browser-cache

REM ���ᮡ�ࠥ� DLL � JSMB LH plugin
mbplugin\python\python mbplugin\plugin\util.py recompile-plugin

REM �஢��塞 �� �� ���㫨 ������������
mbplugin\python\python mbplugin\plugin\util.py check-import

REM �஢��塞 ���४⭮��� ini 䠩���
mbplugin\python\python mbplugin\plugin\util.py check-ini

REM ��⮧���� ��㧥�
mbplugin\python\python mbplugin\plugin\util.py web-server-autostart

REM �஢��塞 playwright
mbplugin\python\python mbplugin\plugin\util.py check-playwright

REM �஢��塞 �� �� ࠡ�⠥� JSMB LH PLUGIN ���⮩ ������
mbplugin\python\python mbplugin\plugin\util.py check-jsmblh simple

REM �஢��塞 �� �� ࠡ�⠥� JSMB LH PLUGIN �१ Chrome
mbplugin\python\python mbplugin\plugin\util.py check-jsmblh chrome

REM �஢��塞 �� �� ࠡ�⠥� DLL PLUGIN
mbplugin\python\python mbplugin\plugin\util.py check-dll

REM �����뢠�� �����
mbplugin\python\python mbplugin\plugin\util.py version -v

timeout 60