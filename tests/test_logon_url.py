import importlib, os, glob
import requests
import conftest  # type: ignore # ignore import error
import pytest


exceptions = ['settings', 'tele2', 'parking_mos', 'sipnet', 'mangooffice']
plugins: list = []

for fn in glob.glob(os.path.join('plugin', '*.py')):
    plugin = os.path.splitext(os.path.split(fn)[-1])[0]
    with open(fn, encoding='utf8') as f:
        if 'def' + ' get_balance(' in f.read():
            plugins.append(plugin)

@pytest.mark.parametrize("plugin", plugins)
def NO_test_logon_url(plugin):
    module = __import__(plugin, globals(), locals(), [], 0)
    importlib.reload(module)  # обновляем модуль, на случай если он менялся
    if hasattr(module, 'login_url'):
        print(f'plugin={plugin}, login_url={module.login_url}')
        url = module.login_url
        response1 = requests.get(url)
        # Проверяем что url вообще открывается
        assert response1.ok, f'Bad url {url} for {plugin}'
