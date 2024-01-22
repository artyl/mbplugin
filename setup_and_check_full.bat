@echo OFF
call "%~dp0\setup_and_check.bat" %*

cd /D "%~dp0\.."
REM очищаем кэши браузера (только в full)
mbplugin\python\python mbplugin\plugin\util.py clear-browser-cache

