@echo off
%~d0 
cd "%~dp0"\..

start "" mbplugin\python\pythonw.exe mbplugin\plugin\httpserver_mobile.py %*
