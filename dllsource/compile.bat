@if "%1"=="" GOTO :EOF
@if "%1"=="dllplugin" GOTO :EOF
@echo Compile to %1.dll
@copy dllplugin.c %1.c 1>nul
@..\tcc\tcc -shared %1.c
@del %1.def
@del %1.c