@ECHO OFF
if "%~1"=="" goto NOPARAM
if "%~2"=="" goto NOPARAM
if "%~3"=="" goto NOPARAM
SET RequestVariable="<Request><ParentWindow>007F09DA</ParentWindow><Login>%2</Login><Password>%3</Password></Request>"
call C:\mbplugin\plugin\mbplugin.bat %1
pause

goto :EOF
:NOPARAM
ECHO Use %0 p_plugin login pass