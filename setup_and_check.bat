@echo OFF
%~d0 

cd "%~dp0"
echo Пересобираем DLL 
call dllsource\compile_all_p.bat

cd "%~dp0"
echo Пересобираем JSMB LH plugin
python\python.exe plugin\compile_all_jsmblh.py

cd "%~dp0"
echo Создаем lnk на run_webserver.bat и помещаем его в автозапуск и запускаем
python\python -c "import os, sys, win32com.client;shell = win32com.client.Dispatch('WScript.Shell');shortcut = shell.CreateShortCut('run_webserver.lnk');shortcut.Targetpath = os.path.abspath('run_webserver.bat');shortcut.save()"
copy run_webserver.lnk "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
start "" "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\run_webserver.lnk"

cd "%~dp0"
echo Проверяем что все работает
call plugin\test_mbplugin_dll_call.bat p_test1 123 456 


