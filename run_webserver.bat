@echo off
cd /D "%~dp0"\..

start "" mbplugin\python\pythonw.exe mbplugin\plugin\httpserver_mobile.py %*
