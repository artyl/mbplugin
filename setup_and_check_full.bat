@echo OFF
call "%~dp0\setup_and_check.bat" %*

cd /D "%~dp0\.."
REM ��頥� ��� ��㧥� (⮫쪮 � full)
mbplugin\python\python mbplugin\plugin\util.py clear-browser-cache

