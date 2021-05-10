@echo OFF
%~d0 
cd "%~dp0"

REM �᫨ ����� mobilebalance - �� ࠡ�⠥�, � � ⮫쪮 ����⠥� ���
if EXIST MobileBalance.exe goto :ERROR1
REM �᫨ ��� Phones.ini - � ⮦� ��室��
if not EXIST phones.ini goto :ERROR1

REM �᫨ ��� mbplugin.ini - ᮧ���� � ����᪠�� ���樠������
if not EXIST mbplugin.ini goto :INIT

if "%1"=="init" goto :INIT

if "%1"=="check" goto :CHECK

if "%1"=="getbalance" goto :GETBALANCE

if "%1"=="getbalancefailed" goto :GETBALANCEFAILED

if "%1"=="updatehtml" goto :UPDATEHTML

GOTO :EOF


@REM ���樠������
:INIT
cd mbplugin\plugin
cd ..\plugin
..\python\python -c "import store;ini=store.ini();ini.read();ini.ini['Options']['sqlitestore']='1';ini.write()"
..\python\python -c "import store;ini=store.ini();ini.read();ini.ini['Options']['createhtmlreport']='1';ini.write()"
..\python\python -c "import store,os;ini=store.ini();ini.read();ini.ini['Options']['balance_html']=os.path.abspath(os.path.join('..','..',balance.html'));ini.write()"
echo %CD%
call ..\setup_and_check.bat %2 %3
GOTO :EOF

@REM �஢�ઠ INI �� ���४⭮���
:CHECK
ECHO �஢��� ᤥ��� �����, ���� �� ���
cd mbplugin\plugin
cd ..\plugin
..\python\python -c "import store;ini=store.ini()"
..\python\python -c "import store;ini=store.ini('phones.ini')"
timeout 15
GOTO :EOF

@REM ����祭�� �����ᮢ
:GETBALANCE
cd mbplugin\plugin
cd ..\plugin
..\python\python.exe -c "import httpserver_mobile,sys;httpserver_mobile.detbalance_standalone(filter=sys.argv[2:])" %*
GOTO :EOF

@REM ����祭�� �����ᮢ (����� �� ��㤠��)
:GETBALANCEFAILED
cd mbplugin\plugin
cd ..\plugin
..\python\python.exe -c "import httpserver_mobile,sys;httpserver_mobile.detbalance_standalone(filter=sys.argv[2:],only_failed=True)" %*
GOTO :EOF

@REM ���������� balance.html
:UPDATEHTML
cd mbplugin\plugin
cd ..\plugin
..\python\python.exe -c "import httpserver_mobile;httpserver_mobile.write_report()" %*
GOTO :EOF

:ERROR1
ECHO � ����� �� ������ ���� 䠩�� Mobilebalance.exe
ECHO � ������ ���� 䠩� Phones.ini
timeout 15
GOTO :EOF