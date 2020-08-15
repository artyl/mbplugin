# -*- coding: utf8 -*-
''' Автор ArtyLa '''
import os, sys, re, logging
import requests
import store

re_csrf = r'(?usi)_csrf_token.*?value="(\w+?)"'

icon = '789C73F235636100033320D600620128666450804840E5A905989999F1CAB359A833B0DBEB90AC9F595A88817F423283D895490C5C31F644EB67E46065E0CEF264103DD3CB20B2AF9924FDEC2EFA0CC23B1B1844CFF531F0E4FB3230097013AD9F7F6A1A582DFF943406663911885BD85888D62F7AAC8381B72E9C81919111A2174833B2B1E2D40F5387AC9FA7D08F4150408841008841348FA0205C3F0F0F2F032F2F1F0307072703171737033FBF2056FD1CEC1C0C6C6CEC0C3CDCBC0C2C9C1C70FDDCDC3C0CEC40391066656503D3C8FA450EB63288EC6D6260773744B811C9FF30F7E2F23FB38C3003FFC414B07A8179B90C2CAA5224851F0CB0596930086DAA6610BB38011C9EA4EA0703166606AE782706D1135DE4E9870226113E06BE966806CE683BB2F4C300232BEE4C4B8C7EBC6603E305008A3A3F17'

def get_balance(login, password, storename=None):
    logging.info(f'start get_balance {login}')
    result = {}
    baseurl = 'https://my.rt.ru/'
    cabinet_url = 'https://my.rt.ru/json/cabinet/'
    headers = {}
    session = store.Session(storename, headers=headers)
    response3 = session.post(cabinet_url, data={})
    # !!! Хоть и возвращает json но 'content-type' - text/html
    if 'accountInfo' in response3.text:
        logging.info(f'Already logoned {login}')
    else:
        # Логинимся
        logging.info(f'relogon {login}')
        session.drop_and_create()
        response1 = session.get(baseurl)
        if response1.status_code != 200:
            raise RuntimeError(f'GET Login page {baseurl} error: status_code {response1.status_code}')
        data = {'_csrf_token': re.findall(re_csrf, response1.text),
                'login': login,
                'password': password,}
        login_url = 'https://my.rt.ru/session/checklogin/'
        response2 = session.post(login_url, data=data)
        if response2.status_code != 200:
            raise RuntimeError(f'POST Login page {login_url} error: status_code {response2.status_code}')
        response3 = session.post(cabinet_url, data={})

    if 'accountInfo' not in response3.text:
        raise RuntimeError(f'Balance (accountInfo) not found on {cabinet_url}')

    result['Balance'] = response3.json().get('accountInfo', {})['balance']
        
    try:
        result['Balance2'] = response3.json().get('bonusAccount',{})['points']
    except Exception:
        logging.info(f'Not found bonusAccount')

    try:
        result['licSchet'] =  response3.json().get('accountInfo', {})['AccountID']
        result['Expired'] =  response3.json().get('accountInfo', {})['daysToLock']
    except Exception:
        logging.info(f'Not found licSchet and Expired')

    try:
        result['anyString'] =  'Статус: ' + response3.json().get('bonusAccount', {})['tier']
    except Exception:
        logging.info(f'Not found anyString (status)')        
    
    session.save_session()
    return result


if __name__ == '__main__':
    print('This is module onlime')
