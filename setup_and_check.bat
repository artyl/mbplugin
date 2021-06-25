@echo OFF
%~d0 
cd "%~dp0"

REM добавляем в sys.path поиск в папке откуда запущен скрипт по умолчанию, в embedded он почему-то выключен
python\python plugin\util.py fix-embedded-python-path

REM Выставляем переменные по значениям в mbplugin.ini
if "%1"=="noweb" python\python plugin\util.py set ini/HttpServer/start_http=0

REM если используем встроенный браузер запускаем playwright install chromium
python\python plugin\util.py install-chromium

REM  очищаем кэши браузера
python\python plugin\util.py clear-browser-cache

REM Пересобираем DLL 
python\python plugin\util.py recompile-dll

REM Пересобираем JSMB LH plugin
python\python plugin\util.py recompile-jsmblh

REM Проверяем что все модули импортируются
python\python plugin\util.py check-import

REM Автозапуск браузера
python\python plugin\util.py autostart-web-server

REM Проверяем playwright
python\python plugin\util.py check-playwright

REM Проверяем что все работает JSMB LH PLUGIN простой плагин
python\python plugin\util.py check-jsmblh simple

REM Проверяем что все работает JSMB LH PLUGIN через Chrome
python\python plugin\util.py check-jsmblh chrome

REM Проверяем что все работает DLL PLUGIN
python\python plugin\util.py check-dll
