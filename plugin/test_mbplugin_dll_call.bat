@ECHO OFF
cd /D "%~dp0"

if "%~1"=="" goto NOPARAM
if "%~2"=="" goto NOPARAM
if "%~3"=="" goto NOPARAM
echo INFO:
..\python\python.exe ..\plugin\dll_call_test.py %1 Info %2 %3
echo EXECUTE:
..\python\python.exe ..\plugin\dll_call_test.py %1 Execute %2 %3
pause

goto :EOF
:NOPARAM
ECHO Use %0 p_plugin login pass