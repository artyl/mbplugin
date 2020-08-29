@echo off
%~d0 
cd "%~dp0"
@REM ..\python\python -c "import re,requests;url=re.findall(r'(?usi)(http://127.0.0.1:.*?/)',open('..\jsmblhplugin\\p_test1_localweb.jsmb').read())[0];print(requests.session().get(url+'sendtgbalance').content.decode('cp1251'))"
@REM Sendtgbalance
..\python\python -c "import requests,store,httpserver_mobile;host=store.options('host',section='HttpServer');port=store.options('port',section='HttpServer');print(requests.get(f'http://{host}:{port}/sendtgbalance').content.decode('cp1251'))"
@REM Subscription
..\python\python -c "import requests,store,httpserver_mobile;host=store.options('host',section='HttpServer');port=store.options('port',section='HttpServer');print(requests.get(f'http://{host}:{port}/sendtgsubscriptions').content.decode('cp1251'))"
