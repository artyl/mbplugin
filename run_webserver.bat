@echo off
%~d0 
cd "%~dp0"\plugin

start "" ..\python\pythonw.exe ..\plugin\httpserver_mobile.py