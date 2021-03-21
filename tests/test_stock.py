import re
import pytest
import requests
import conftest
import stock  # pylint: disable=import-error

def test_sodexo():
    assert stock.get_yahoo('YAHOO','TSLA',1)['price'] > 0
    assert stock.get_finex('FINEX', 'FXIT', 1)['price'] > 0
    assert stock.get_moex('M_TQBR', 'TATNP',1)['price'] > 0
    assert stock.get_moex('M_TQTF', 'FXIT',1)['price'] > 0
    assert stock.get_moex('M_TQTD', 'FXIT',1)['price'] > 0

    assert stock.get_balance('broker_ru','123', 'test_stock')['Balance'] > 0

