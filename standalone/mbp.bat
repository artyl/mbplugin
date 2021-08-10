@echo OFF
%~d0 
cd "%~dp0"

if EXIST ..\plugin\util.py (
    cd ..\..
    copy mbplugin\standalone\%~nx0 .
    mbplugin\python\python mbplugin\plugin\util.py init
    mbplugin\python\python mbplugin\plugin\util.py pip-update -q
    mbplugin\python\python mbplugin\plugin\util.py install-chromium
    mbplugin\python\python mbplugin\plugin\util.py check-import
    mbplugin\python\python mbplugin\plugin\util.py check-ini
    mbplugin\python\python mbplugin\plugin\util.py clear-browser-cache
    mbplugin\python\python mbplugin\plugin\util.py check-playwright
    mbplugin\python\python mbplugin\plugin\util.py web-server-autostart
    IF NOT "%PACKET_MODE%"=="ON" timeout 30
    GOTO :EOF
)

mbplugin\python\python mbplugin\plugin\util.py %*
