@echo OFF
%~d0 
cd "%~dp0"

REM Если лежит mobilebalance - не работаем, а то только запутаем всех
if EXIST MobileBalance.exe goto :ERROR1
REM Если нет Phones.ini - то тоже выходит
if not EXIST phones.ini goto :ERROR1

REM Если нет mbplugin.ini - создаем и запускаем инициализацию
if not EXIST mbplugin.ini goto :INIT

if "%1"=="init" goto :INIT

if "%1"=="check" goto :CHECK

if "%1"=="getbalance" goto :GETBALANCE

if "%1"=="updatehtml" goto :UPDATEHTML

GOTO :EOF


@REM Инициализация
:INIT
cd mbplugin\plugin
cd ..\plugin
..\python\python -c "import store;ini=store.ini();ini.read();ini.ini['Options']['sqlitestore']='1';ini.write()"
..\python\python -c "import store;ini=store.ini();ini.read();ini.ini['Options']['createhtmlreport']='1';ini.write()"
..\python\python -c "import store,os;ini=store.ini();ini.read();ini.ini['Options']['balance_html']=os.path.abspath('..\\..\\balance.html');ini.write()"
echo %CD%
call ..\setup_and_check.bat %2 %3
GOTO :EOF

@REM Проверка INI на корректность
:CHECK
ECHO Проверку сделаю позже, пока ее нет
cd mbplugin\plugin
cd ..\plugin
..\python\python -c "import store;ini=store.ini()"
..\python\python -c "import store;ini=store.ini('phones.ini')"
timeout 15
GOTO :EOF

@REM Получение балансов
:GETBALANCE
cd mbplugin\plugin
cd ..\plugin
..\python\python.exe -c "import httpserver_mobile,sys;httpserver_mobile.detbalance_standalone(filter=sys.argv[2:])" %*
GOTO :EOF

@REM Обновление balance.html
:UPDATEHTML
cd mbplugin\plugin
cd ..\plugin
..\python\python.exe -c "import httpserver_mobile;httpserver_mobile.write_report()" %*
GOTO :EOF

:ERROR1
ECHO В папке не должно быть файла Mobilebalance.exe
ECHO И должен быть файл Phones.ini
timeout 15
GOTO :EOF