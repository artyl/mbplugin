'Проверка установки с нуля'
import os, tempfile, shutil
import conftest  # type: ignore # ignore import error
import settings  # pylint: disable=import-error
import store  # pylint: disable=import-error


def test_zeroinstall():
    with tempfile.TemporaryDirectory() as tmpname:
        settings.mbplugin_root_path = tmpname
        os.makedirs(os.path.join(tmpname, 'mbplugin', 'store'))
        os.makedirs(os.path.join(tmpname, 'mbplugin', 'log'))
        os.makedirs(os.path.join(tmpname, 'mbplugin', 'db'))
        shutil.copy(os.path.join(conftest.data_path, 'phones.ini'), os.path.join(tmpname, 'phones.ini'))
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
        #breakpoint()
        #print(f'Check {ini.ini_to_json()}')
        #tmp.cleanup()
