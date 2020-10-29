@ECHO OFF
%~d0 
cd "%~dp0"

..\python\python -c "import pyppeteeradd;pyppeteeradd.hide_chrome(hide=False)"
