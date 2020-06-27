# -*- coding: utf8 -*-
''' Автор ArtyLa '''
import os, sys, re, logging
import requests
import store

def get_balance(login, password, storename=None):
    requests.packages.urllib3.disable_warnings()
    result = {}
    session = requests.Session()
    baseurl = 'http://strelkacard.ru'
    url = "https://strelkacard.ru/api/cards/status/?cardnum=" + login + "&cardtypeid=3ae427a1-0f17-4524-acb1-a3f50090a8f3"
    response2 = session.get(url, headers={'Referer': baseurl + '/'}, verify=False)
    logging.debug(response2.text)
    # html=u'<html><http-equiv="Content-type" content="text/html; charset=windows-1251" /><p id="Balance">%s<p id="TarifPlan">%s</html>' % (
    result['Balance'] = response2.json()['balance']/100.
    if response2.json().get('emergencyblocked', False):
        result['BlockStatus'] = 'Emergency Blocked'
    if response2.json().get('cardblocked', False):
        result['BlockStatus'] = 'Card Blocked'
    return result


if __name__ == '__main__':
    print('This is module strelka')
