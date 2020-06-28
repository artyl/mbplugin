# -*- coding: utf8 -*-
''' Получение котировок с finance.yahoo.com в логин код ценной бумаги
    https://finance.yahoo.com/quote/AAPL
    https://query1.finance.yahoo.com/v8/finance/chart/AAPL '''
''' Автор ArtyLa '''
import os, sys, re, time, logging
import requests
import store, settings

icon = '789C73F235636100033320D600620128666450804840E591C125C68461853F6DB9C0F0FFFF7F8667C5CBC9D27FCFB90BACFFE7FDD70C97599248D7EFD603D60FC20F822633DCD4AC64F879EF15C3B7937719AE0A641276FFF64B70FD5F0EDE60781C370BCEBF63D18457EF2DED6A86FFFFFE33FC7EF991E1D7C337103DE64D0CCF8A96313C499B4FD0EE77730E82F5BC6ADBC2F0A26A0D98FD6EE11186A7598B18FEBCFDC2F0F3EE2B862B5C6958F55E13CF63F8F7FD17C3FFBFFF186E289640F83F7F83F12D9D6A867FDF7E81CD7B9ABE00ABFEDBC6F50C2F1B36303CCD5808177B9C38072C06927B3BEB0058FF8FEBCF182E3125921C2F37B52A8161F30F6CC67DEF7EB2D2C68755A7187EBFFAC4F07EF1B1014FE7D4C0F3183D18000E448007'

def get_balance(login, password, storename=None):
    result = {}
    session = requests.Session()
    url = time.strftime(f'https://query1.finance.yahoo.com/v8/finance/chart/{login}')
    response = session.get(url)
    meta = response.json()['chart']['result'][0]['meta']
    meta['regularMarketPrice']
    result['Balance'] = meta['regularMarketPrice']
    return result


if __name__ == '__main__':
    print('This is module finance.yahoo.com')
