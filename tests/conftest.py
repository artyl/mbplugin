import pytest
import sys, os
sys.path.insert(0, os.path.abspath('plugin'))

import settings  # pylint: disable=import-error

data_path = os.path.abspath(os.path.join('tests', 'data'))
settings.mbplugin_root_path = data_path
settings.mbplugin_ini_path = data_path
settings.ini_codepage = 'cp1251'
print(os.path.abspath('plugin'))

def pytest_addoption(parser):
    parser.addoption(
        "--runslow", action="store_true", default=False, help="run slow tests"
    )

def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow to run")

def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslow"):
        #  опция --runslow запрошена в командной строке: медленные тесты не пропускаем
        return
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)

def ini_compare(fn1, fn2):
    'Compare ini files ignore crlf'
    with open(fn1, encoding=settings.ini_codepage ) as f1, open(fn2, encoding=settings.ini_codepage ) as f2:
        data1 = f1.read().replace('\r\n', '\n')
        data2 = f2.read().replace('\r\n', '\n')
    return data1 == data2

# https://habr.com/ru/post/448782
# debug insert assert 0 and use py.test --pdb 
# python -m pytest tests/test_store.py::test_ini_class_phones_ini_writ -vv --pdb