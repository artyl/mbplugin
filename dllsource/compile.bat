@echo OFF
cd /D "%~dp0"
set FULLPATH=%~dp0

if "%1"=="" GOTO :EOF
if "%1"=="dllplugin" GOTO :EOF
@REM echo Compile to %1.dll
copy dllplugin.c %1.c 1>nul
..\tcc\tcc -shared "%FULLPATH%%1.c"
del %1.def
del %1.c