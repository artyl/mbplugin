@echo OFF
%~d0 
cd "%~dp0\.."
set MBPLUGIN_WRITE_DIAG=YES
if EXIST mbplugin\log\setup_diag.txt del mbplugin\log\setup_diag.txt 

REM добавляем в sys.path поиск в папке откуда запущен скрипт по умолчанию, в embedded он почему-то выключен
mbplugin\python\python mbplugin\plugin\util.py fix-embedded-python-path

REM Выставляем переменные по значениям в mbplugin.ini
if "%1"=="noweb" mbplugin\python\python mbplugin\plugin\util.py set ini/HttpServer/start_http=0

REM если используем встроенный браузер запускаем playwright install chromium
mbplugin\python\python mbplugin\plugin\util.py install-chromium

REM очищаем кэши браузера (только в full)
mbplugin\python\python mbplugin\plugin\util.py clear-browser-cache

REM Пересобираем DLL и JSMB LH plugin
mbplugin\python\python mbplugin\plugin\util.py recompile-plugin

REM Проверяем что все модули импортируются
mbplugin\python\python mbplugin\plugin\util.py check-import

REM Проверяем корректность ini файлов
mbplugin\python\python mbplugin\plugin\util.py check-ini

REM Автозапуск браузера
mbplugin\python\python mbplugin\plugin\util.py web-server-autostart

REM Проверяем playwright
mbplugin\python\python mbplugin\plugin\util.py check-playwright

REM Проверяем что все работает JSMB LH PLUGIN простой плагин
mbplugin\python\python mbplugin\plugin\util.py check-jsmblh simple

REM Проверяем что все работает JSMB LH PLUGIN через Chrome
mbplugin\python\python mbplugin\plugin\util.py check-jsmblh chrome

REM Проверяем что все работает DLL PLUGIN
mbplugin\python\python mbplugin\plugin\util.py check-dll

REM Показываем версию
mbplugin\python\python mbplugin\plugin\util.py version -v

timeout 60