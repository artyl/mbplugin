if "%1"=="" GOTO :EOF
if "%1"=="dllplugin" GOTO :EOF
del *.d*
del test_dllplugin.exe
copy dllplugin.c %1.c
..\tcc\tcc -shared %1.c
..\tcc\tcc test_dllplugin.c %1.def
test_dllplugin.exe
del *.d*
del test_dllplugin.exe
