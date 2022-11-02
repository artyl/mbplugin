import os, shutil
import pytest
import conftest  # type: ignore # ignore import error
import settings, stock  # pylint: disable=import-error


def setup():
    os.makedirs(os.path.join(settings.mbplugin_root_path, 'mbplugin', 'log'), exist_ok=True)
    os.makedirs(os.path.join(settings.mbplugin_root_path, 'mbplugin', 'store'), exist_ok=True)
    assert os.path.split(__file__)[0] == os.path.split(settings.mbplugin_ini_path)[0], f'Folder {settings.mbplugin_ini_path} is not subfolder for test {__file__}'


    # def teardown():
    # assert os.path.split(__file__)[0] == os.path.split(settings.mbplugin_ini_path)[0], f'Folder {settings.mbplugin_ini_path} is not subfolder for test {__file__}'
    # ini_path = os.path.join(settings.mbplugin_ini_path, 'mbplugin.ini')
    # if 'mbplugin\\tests\\data' in ini_path and os.path.exists(ini_path):
    #     os.remove(ini_path)
    # print ("basic teardown into conftest")


def test_stock(prepare_ini):
    assert stock.get_yahoo('YAHOO', 'TSLA', 1)['price'] > 0
    assert stock.get_finex('FINEX', 'FXIT', 1)['price'] > 0
    assert stock.get_moex('M_TQBR', 'TATNP', 1)['price'] > 0
    assert stock.get_moex('M_TQTF', 'FXIT', 1)['price'] > 0
    assert stock.get_moex('M_TQTD', 'FXIT', 1)['price'] > 0

    assert stock.get_balance('broker_ru', '123', 'test_stock')['Balance'] > 0
