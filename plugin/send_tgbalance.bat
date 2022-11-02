@echo off
%~d0 
cd "%~dp0"
@REM ..\python\python -c "import re,requests;url=re.findall(r'(?usi)(http://127.0.0.1:.*?/)',open('..\jsmblhplugin\\p_test1_localweb.jsmb').read())[0];print(requests.session().get(url+'sendtgbalance').content.decode('cp1251'))"
@REM Sendtgbalance
..\python\python -c "import requests,store;store.switch_to_mb_mode();port=store.options('port',section='HttpServer');print(requests.get(f'http://localhost:{port}/sendtgbalance').content.decode('cp1251'))"
@REM Subscription
..\python\python -c "import requests,store;store.switch_to_mb_mode();port=store.options('port',section='HttpServer');print(requests.get(f'http://localhost:{port}/sendtgsubscriptions').content.decode('cp1251'))"
