@echo OFF
%~d0 
cd "%~dp0"

if "%mbpluginpythonpath%"=="" SET mbpluginpythonpath=mbplugin\python

if EXIST ..\plugin\util.py (
    cd ..\..
    copy mbplugin\standalone\%~nx0 .
    %mbpluginpythonpath%\python mbplugin\plugin\util.py init
    %mbpluginpythonpath%\python mbplugin\plugin\util.py web-server stop -f
    %mbpluginpythonpath%\python mbplugin\plugin\util.py pip-update -q
    %mbpluginpythonpath%\python mbplugin\plugin\util.py install-chromium
    %mbpluginpythonpath%\python mbplugin\plugin\util.py check-import
    %mbpluginpythonpath%\python mbplugin\plugin\util.py check-ini
    %mbpluginpythonpath%\python mbplugin\plugin\util.py clear-browser-cache
    %mbpluginpythonpath%\python mbplugin\plugin\util.py check-playwright
    %mbpluginpythonpath%\python mbplugin\plugin\util.py web-server-autostart
    %mbpluginpythonpath%\python mbplugin\plugin\util.py version -v
    IF NOT "%PACKET_MODE%"=="ON" timeout 30
    GOTO :EOF
)

%mbpluginpythonpath%\python mbplugin\plugin\util.py %*
