@echo OFF
@REM clean:
@REM git clean -fXd
set "ptime= "
where ptime >nul 2>1&
if %errorlevel%==0 set ptime=ptime

if NOT "%1"=="" goto %1
ECHO RUN build clean/test/build/fixup

goto :EOF
@REM @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ test
:coverage
cd /D "%~dp0"
call python\python -m coverage run -m pytest tests %2 %3 %4 %5 %6 %7 %8 %9
echo coverage html
call python\python -m coverage html
@rem call start htmlcov\index.html 
echo %errorlevel%
goto :EOF
@REM @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ test
:test

cd /D "%~dp0"
call python\python -m pip install -r docker\requirements_pytest.txt 
call python\python -m pytest tests %2 %3 %4 %5 %6 %7 %8 %9
echo %errorlevel%
goto :EOF
@REM @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ fixup
:fixup
cd /D "%~dp0\plugin"
@REM Fix docker playwright container version by playwright in python lib
..\python\python -c "import util;util.mbplugin_dockerfile_version()"
@REM Fix mbplugin_ini.md by setting.py
..\python\python -c "import util;util.mbplugin_ini_md_gen()"
goto :EOF
@REM @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ run
:run
goto :EOF
@REM @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ clean
:clean
cd /D "%~dp0"
if NOT EXIST ..\mbplugin\store\git-clear-protected (git clean -fXd) ELSE echo git-clear-protected
if exist ..\mbplugin\dist rd ..\mbplugin\dist /S /Q

goto :EOF
@REM @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ build
:build
cd /D "%~dp0"
if not exist dist mkdir dist

SET PACKET_MODE=ON

where 7z >nul 2>&1
if NOT "%errorlevel%"=="0" (
echo Not found 7z
goto :EOF
)

where curl >nul 2>&1
if NOT "%errorlevel%"=="0" (
echo Not found curl
goto :EOF
)

cd /D "%~dp0\.."
call mbplugin\tcc\get_tcc.bat
cd /D "%~dp0\.."
if NOT EXIST mbplugin\tcc\tcc.exe (
    ECHO Error install tcc
    GOTO :EOF
)

cd /D "%~dp0\.."
SET PYTHONDONTWRITEBYTECODE=1
call mbplugin\python\get_python.bat
cd /D "%~dp0\.."
if NOT EXIST mbplugin\python\Lib\site-packages\playwright\__init__.py (
    ECHO Error install python
    GOTO :EOF
)

cd /D "%~dp0\.."
call mbplugin\standalone\mbp
cd /D "%~dp0\.."
if NOT EXIST mbp.bat (
    ECHO Error install mbp
    GOTO :EOF
)

cd /D "%~dp0\..\mbplugin\plugin"
..\python\python -c "import util;util.mbplugin_ini_md_gen()"
..\python\python -c "import util;util.mbplugin_dockerfile_version()"
call git diff --exit-code
if NOT "%errorlevel%"=="0" (
    ECHO Not all change will be commited
    GOTO :EOF
)

cd /D "%~dp0\.."
call mbplugin\setup_and_check_full.bat
cd /D "%~dp0\.."
if NOT EXIST balance.html (
    ECHO Error setup_and_check
    GOTO :EOF
)
if NOT EXIST mbplugin\store\headless (
    ECHO Error setup_and_check
    GOTO :EOF
)

cd /D "%~dp0\.."
call mbp clear-browser-cache
cd /D "%~dp0\.."
if EXIST mbplugin\store\headless (
    ECHO Error setup_and_check
    GOTO :EOF
)

cd /D "%~dp0"
call python\python -m pip install -r docker\requirements_pytest.txt 
call python\python -m pytest tests
call python\python -m pytest tests
if "%ERRORLEVEL%"==1  (
    ECHO Error tests
    GOTO :EOF
)
call python\python -m pip uninstall -y -r docker\requirements_pytest.txt 
call python\python -m pip install -r docker\requirements_win.txt

cd /D "%~dp0\.."
call mbplugin\python\python mbplugin\python\remove__pycache__.py
cd /D "%~dp0\.."
if EXIST mbplugin\python\__pycache__  (
    ECHO Error __pycache__ 
    GOTO :EOF
)

cd /D "%~dp0\.."
call mbp web-server stop
timeout 5
cd /D "%~dp0\.."
if EXIST mbplugin\store\web-server.pid (
    ECHO Error stop web-server
    GOTO :EOF
)

cd /D "%~dp0\.."
del mbplugin\log\*.log
del mbplugin\log\*.png
del mbplugin\store\mbplugin.ini.bak.zip
del mbplugin\python\scripts\*.exe

cd /D "%~dp0"
for /F "tokens=1 delims=#" %%T IN ('git rev-parse HEAD') DO set mbpluginhead=%%T
for /F "tokens=3 delims= " %%T IN ('find "## mbplugin v1." changelist.md') DO set mbpluginversion=%%T
curl -Lk https://github.com/artyl/mbplugin/archive/%mbpluginhead%.zip -o pack\current.zip
7z rn pack\current.zip mbplugin-%mbpluginhead% mbplugin
copy pack\current.zip dist\mbplugin_bare.%mbpluginversion%.zip
call git-restore-mtime

cd /D "%~dp0\.."
7z a -tzip mbplugin\dist\mbplugin.%mbpluginversion%.zip mbplugin -xr0!mbplugin\.git -xr0!mbplugin\dist -xr!*.log

cd /D "%~dp0\plugin"
..\python\python -c "import updateengine;updateengine.create_signature()"

goto :EOF
@REM @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
