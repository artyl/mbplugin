import os
import pytest
import conftest  # type: ignore # ignore import error
import settings, stock  # pylint: disable=import-error

def setup():
    os.makedirs(os.path.join(settings.mbplugin_root_path, 'mbplugin', 'log'), exist_ok=True)
    os.makedirs(os.path.join(settings.mbplugin_root_path, 'mbplugin', 'store'), exist_ok=True)
 
def teardown():
    pass # print ("basic teardown into conftest")

def test_stock():
    assert stock.get_yahoo('YAHOO','TSLA',1)['price'] > 0
    assert stock.get_finex('FINEX', 'FXIT', 1)['price'] > 0
    assert stock.get_moex('M_TQBR', 'TATNP',1)['price'] > 0
    assert stock.get_moex('M_TQTF', 'FXIT',1)['price'] > 0
    assert stock.get_moex('M_TQTD', 'FXIT',1)['price'] > 0

    assert stock.get_balance('broker_ru','123', 'test_stock')['Balance'] > 0

