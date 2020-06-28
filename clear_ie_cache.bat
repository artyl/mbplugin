Taskkill /IM mobilebalance.exe /F
rd "%LOCALAPPDATA%\Microsoft\Windows\Temporary Internet Files\Content.IE5" /S /Q
if exist ..\MobileBalance.exe start ..\MobileBalance.exe
if exist ..\..\MobileBalance.exe start ..\..\MobileBalance.exe
if exist ..\..\..\MobileBalance.exe start ..\..\..\MobileBalance.exe
