import pytest
import sys, os, asyncio
sys.path.insert(0, os.path.abspath('plugin'))

import settings  # pylint: disable=import-error
import pyppeteeradd as pa  # pylint: disable=import-error


settings.mbplugin_root_path = 'tests\\data'

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
