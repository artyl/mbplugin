@ECHO OFF
%~d0 
cd "%~dp0"

..\python\python -c "import browsercontroller;browsercontroller.hide_chrome(hide=False)"
