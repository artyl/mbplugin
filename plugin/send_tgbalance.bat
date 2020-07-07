%~d0 
cd "%~dp0"
..\python\python -c "import re,requests;url=re.findall(r'(?usi)(http://127.0.0.1:.*?/)',open('..\jsmblhplugin\\p_test1_localweb.jsmb').read())[0];print(requests.session().get(url+'sendtgbalance').content.decode('cp1251'))"
