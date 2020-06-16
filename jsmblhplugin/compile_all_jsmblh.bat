@ECHO OFF
%~d0 
cd "%~dp0"

@..\python\python -c "import os,glob;tmpl=open('_template_localweb.jsmb',encoding='cp1251').read();fl=['p_'+os.path.splitext(os.path.split(fn)[1])[0] for fn in glob.glob('..\\plugin\\*.py') if 'def get_balance(' in open(fn,encoding='utf8').read()];[open(fn+'_localweb.jsmb','w').write(tmpl.replace('{{pluginname}}',fn)) for fn in fl]"
