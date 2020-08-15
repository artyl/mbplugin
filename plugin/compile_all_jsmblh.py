import os, sys, re, glob
import settings, store

pluginpath = os.path.split(sys.argv[0])[0]
port = store.options('port', section='HttpServer')
tmpl = open(os.path.join(pluginpath, '..\\jsmblhplugin\\_template_localweb.jsmb'), encoding='cp1251').read()

for fn in glob.glob(os.path.join(pluginpath, '..\\plugin\\*.py')):
    if ('def' + ' get_balance(') in open(fn, encoding='utf8').read():
        plugin = os.path.splitext(os.path.split(fn)[1])[0]
        fl = 'p_' + plugin
        module = __import__(plugin, globals(), locals(), [], 0)
        data = tmpl.replace('{{pluginname}}', fl).replace('{{port}}', port)
        if hasattr(module,'icon'):
            data = re.sub(r'//\s*Icon\s*:\s*\S*', f'// Icon      : {module.icon}', data)
        plugin_name = os.path.join(pluginpath, '..\\jsmblhplugin', fl+'_localweb.jsmb')
        open(plugin_name, 'w').write(data)
