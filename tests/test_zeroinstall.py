'Проверка установки с нуля'
import re, os, tempfile
import pytest
import requests
import conftest
import settings  # pylint: disable=import-error
import store  # pylint: disable=import-error


def test_zeroinstall():
    tmp = tempfile.TemporaryDirectory()
    settings.mbplugin_root_path = tmp.name
    ini = store.ini()
    print(f'Zeroinstall ini={os.path.abspath(ini.inipath)}')
    print(f'Zeroinstall ini exists={os.path.exists(os.path.abspath(ini.inipath))}')
    assert os.path.exists(os.path.abspath(ini.inipath)) == False
    print(f'Check {ini.read()}')
    assert os.path.exists(os.path.abspath(ini.inipath)) == True
    # assert re.search(chk, response1.text) is not None
    ini.save_bak()
    ini.ini_to_json()
    ini.write()
    ini.create()
    assert ini.find_files_up(ini.fn) == os.path.abspath(ini.inipath)
    print(f'{list(ini.ini.keys())}')
    #breakpoint()
    #print(f'Check {ini.ini_to_json()}')
    tmp.cleanup()
