@echo OFF
%~d0 
@REM clean:
@REM git clean -fXd

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

cd "%~dp0\.."
call mbplugin\tcc\get_tcc.bat
cd "%~dp0\.."
if NOT EXIST mbplugin\tcc\tcc.exe (
    ECHO Error install tcc
    GOTO :EOF
)

cd "%~dp0\.."
SET PYTHONDONTWRITEBYTECODE=1
call mbplugin\python\get_python.bat
cd "%~dp0\.."
if NOT EXIST mbplugin\python\Lib\site-packages\playwright\__init__.py (
    ECHO Error install python
    GOTO :EOF
)

cd "%~dp0\.."
call mbplugin\standalone\mbp
cd "%~dp0\.."
if NOT EXIST mbp.bat (
    ECHO Error install mbp
    GOTO :EOF
)

cd "%~dp0\.."
call mbplugin\setup_and_check.bat
cd "%~dp0\.."
if NOT EXIST balance.html (
    ECHO Error setup_and_check
    GOTO :EOF
)
if NOT EXIST mbplugin\store\headless (
    ECHO Error setup_and_check
    GOTO :EOF
)

cd "%~dp0\.."
call mbp clear-browser-cache
cd "%~dp0\.."
if EXIST mbplugin\store\headless (
    ECHO Error setup_and_check
    GOTO :EOF
)

cd "%~dp0\.."
call mbplugin\python\python mbplugin\python\remove__pycache__.py
cd "%~dp0\.."
if EXIST mbplugin\python\__pycache__  (
    ECHO Error __pycache__ 
    GOTO :EOF
)

cd "%~dp0\.."
call mbp web-server stop
timeout 5
cd "%~dp0\.."
if EXIST mbplugin\store\web-server.pid (
    ECHO Error stop web-server
    GOTO :EOF
)


cd "%~dp0\.."
del mbplugin\log\*.log
del mbplugin\log\*.png
del mbplugin\store\mbplugin.ini.bak.zip
del mbplugin\python\scripts\*.exe

cd "%~dp0"
call git-restore-mtime

cd "%~dp0\.."
7z a -tzip mbplugin mbplugin
