import os, sys, glob

pluginpath = os.path.split(os.path.abspath(sys.argv[0]))[0]
if pluginpath not in sys.path:
    sys.path.append(pluginpath)
import settings, store

port = store.read_ini()['HttpServer'].get('port', settings.port)
tmpl = open(os.path.join(pluginpath, '..\\jsmblhplugin\\_template_localweb.jsmb'), encoding='cp1251').read()

for fn in glob.glob(os.path.join(pluginpath, '..\\plugin\\*.py')):
    if 'def get_balance(' in open(fn, encoding='utf8').read():
        fl = 'p_'+os.path.splitext(os.path.split(fn)[1])[0]
        data = tmpl.replace('{{pluginname}}', fl).replace('{{port}}', port)
        plugin_name = os.path.join(pluginpath, '..\\jsmblhplugin', fl+'_localweb.jsmb')
        open(plugin_name, 'w').write(data)
