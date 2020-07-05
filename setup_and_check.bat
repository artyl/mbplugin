@echo OFF
%~d0 

@REM добавляем в sys.path поиск в папке откуда запущен скрипт по умолчанию, в embedded он почему-то выключен
cd python 
..\python\python -c "txt='''import os,sys\nsys.path.insert(0,os.path.split(sys.argv[0])[0])''';open('sitecustomize.py','w').write(txt)"


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
start "" /MIN "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\run_webserver.lnk"

cd "%~dp0"
echo Проверяем что все работает JSMB LH PLUGIN
python\python -c "import re,requests;url=re.findall(r'(?usi)(http://127.0.0.1:.*?/)',open('jsmblhplugin\\p_test1_localweb.jsmb').read())[0];print(requests.session().get(url+'getbalance/p_test1/123/456/789').content.decode('cp1251'))"

cd "%~dp0"
echo Проверяем что все работает DLL PLUGIN
call plugin\test_mbplugin_dll_call.bat p_test1 123 456 
