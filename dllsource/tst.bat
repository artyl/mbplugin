%~d0 
cd "%~dp0"
set FULLPATH=%~dp0

if "%1"=="" GOTO :EOF
if "%1"=="dllplugin" GOTO :EOF
del *.d*
del test_dllplugin.exe
copy dllplugin.c %1.c
..\tcc\tcc -shared %FULLPATH%%1.c
..\tcc\tcc %FULLPATH%test_dllplugin.c %1.def
test_dllplugin.exe
del %1.c
del *.d*
del test_dllplugin.exe
