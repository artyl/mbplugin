@echo OFF
%~d0 
cd "%~dp0"

REM Если нет mbplugin.ini - создаем и запускаем инициализацию
if not EXIST mbplugin.ini mbplugin\python\python mbplugin\plugin\util.py standalone-init

if "%1"=="init" mbplugin\python\python mbplugin\plugin\util.py standalone-init
if "%1"=="init" mbplugin\setup_and_check.bat %2 %3

if "%1"=="check" mbplugin\python\python mbplugin\plugin\util.py check-mbplugin-ini

if "%1"=="getbalance" mbplugin\python\python mbplugin\plugin\util.py standalone-get-balance --only_failed

if "%1"=="getbalancefailed" mbplugin\python\python mbplugin\plugin\util.py standalone-get-balance --only_failed

if "%1"=="updatehtml" mbplugin\python\python mbplugin\plugin\util.py refresh-balance-html


