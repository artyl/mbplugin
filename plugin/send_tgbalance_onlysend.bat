@ECHO OFF
%~d0 
cd "%~dp0"
rem PING over requests
REM ..\python\python -c "import requests,store,httpserver_mobile;httpserver_mobile.send_telegram_over_requests(text='PING')"
rem Balanse over requests
..\python\python -c "import requests,store,httpserver_mobile;httpserver_mobile.send_telegram_over_requests()"
