import os
import pytest
import conftest  # type: ignore # ignore import error
import currency  # pylint: disable=import-error


def test_stock():
    assert currency.get_balance('USD','123')['Balance'] > 0
    assert currency.get_balance('WWW','123') == {}
    assert currency.get_balance('RBC USD','123')['Balance'] > 0
    assert currency.get_balance('RBC_EUR','123')['Balance'] > 0
    assert currency.get_balance('MOEX_TATNP','123')['Balance'] > 0
    assert currency.get_balance('MOEX_USD/RUB','123')['Balance'] > 0
    # assert currency.get_balance('MOEX EUR/RUB','123')['Balance'] > 0  # no longer published
    assert currency.get_balance('MOEX_currency_selt_x_EUR_RUB__TOM','123')['Balance'] > 0
    assert currency.get_balance('MOEX_currency_selt_x_USD000UTSTOM','123')['Balance'] > 0
    assert currency.get_balance('MOEX_stock_shares_x_AFLT','123')['Balance'] > 0
    assert currency.get_balance('MOEX_stock_shares_x_TATNP','123')['Balance'] > 0
    assert currency.get_balance('MOEX_stock_shares_TQTD_TECH','123')['Balance'] > 0
    # assert currency.get_balance('MOEX_stock_shares_TTTTTT','123')['Balance'] == {}
