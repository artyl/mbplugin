'Проверка установки с нуля'
import os, tempfile, shutil
import conftest  # type: ignore # ignore import error
import settings  # pylint: disable=import-error
import store  # pylint: disable=import-error

def do_test_zeroinstall():
    os.makedirs(os.path.join(settings.mbplugin_root_path, 'mbplugin', 'store'))
    os.makedirs(os.path.join(settings.mbplugin_root_path, 'mbplugin', 'log'))
    os.makedirs(os.path.join(settings.mbplugin_root_path, 'mbplugin', 'db'))
    shutil.copy(os.path.join(conftest.data_path, 'phones.ini'), os.path.join(settings.mbplugin_ini_path, 'phones.ini'))    
    ini = store.ini()
    print(f'Zeroinstall ini={os.path.abspath(ini.inipath)}')
    print(f'Zeroinstall ini exists={os.path.exists(os.path.abspath(ini.inipath))}')
    assert os.path.exists(os.path.abspath(ini.inipath)) == False
    ini.write()
    print(f'Check {ini.read()}')
    assert os.path.exists(os.path.abspath(ini.inipath)) == True
    # assert re.search(chk, response1.text) is not None
    ini.save_bak()
    ini.ini_to_json()
    ini.write()
    ini.create()
    assert ini.find_files_up(ini.fn) == os.path.abspath(ini.inipath)
    print(f'{list(ini.ini.keys())}')

def test_zeroinstall():
    with tempfile.TemporaryDirectory() as tmpname:
        settings.mbplugin_ini_path = tmpname
        settings.mbplugin_root_path = settings.mbplugin_ini_path
        do_test_zeroinstall()


def test_zeroinstall_multifolder():
    with tempfile.TemporaryDirectory() as tmpname:
        settings.mbplugin_ini_path = tmpname
        settings.mbplugin_root_path = os.path.join(tmpname, 'folder1', 'folder2')
        do_test_zeroinstall()