@echo OFF

cd /D "%~dp0\.."
REM очищаем кэши браузера
mbplugin\python\python mbplugin\plugin\util.py clear-browser-cache

