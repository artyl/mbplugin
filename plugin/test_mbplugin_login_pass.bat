@ECHO OFF
%~d0 
cd "%~dp0"

if "%~1"=="" goto NOPARAM
if "%~2"=="" goto NOPARAM
if "%~3"=="" goto NOPARAM
SET RequestVariable="<Request><ParentWindow>007F09DA</ParentWindow><Login>%2</Login><Password>%3</Password></Request>"
call ..\plugin\mbplugin.bat %1
pause

goto :EOF
:NOPARAM
ECHO Use %0 p_plugin login pass