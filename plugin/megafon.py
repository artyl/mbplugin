# -*- coding: utf8 -*- 
import sys;sys.dont_write_bytecode = True
import os, sys, io, re, logging
from PIL import Image, ImageTk
import tkinter.tix as Tix
import requests, bs4
import store, settings

interUnit = 'GB'

def get_balance(login, password, storename=None):
    result={}
    pages=[]
    session = store.load_session(storename)
    if session is None:  # Сессия не сохранена - создаем
        session = requests.Session()
    response3 = session.get('https://lk.megafon.ru/api/lk/main/atourexpense')
    if 'json' in response3.headers.get('content-type') and 'balance' in response3.text:
        logging.info('Old session is ok')
    else: # Нет, логинимся
        logging.info('Old session is bad, relogin')
        response1 = session.get('https://lk.megafon.ru/login/')
        if response1.status_code != 200:
            raise RuntimeError(f'GET Login page error: status_code {response1.status_code}!=200')
        pages.append(response1.text)
        csrf = re.search('(?usi)name="CSRF" value="([^\"]+)"',response1.text)
        data = {'CSRF': csrf, 'j_username': f'+7{login}', 'j_password': password}
        response2 = session.post('https://lk.megafon.ru/dologin/', data=data)
        if response2.status_code != 200:
            raise RuntimeError(f'POST Login page error: status_code {response2.status_code}!=200')        
        pages.append(response2.text)
        response3 = session.get('https://lk.megafon.ru/api/lk/main/atourexpense')
        if response3.status_code != 200 or 'json' not in response3.headers.get('content-type'):
            raise RuntimeError(f'Get Balance page not return json: status_code={response2.status_code} {response3.headers.get("content-type")}')
        pages.append(response3.text)
        if 'balance' not in response3.text:
            raise RuntimeError(f'Get Balance page not return balance: status_code={response2.status_code} {response3.text}')

    result['Balance'] = response3.json().get('balance',0)
    result['KreditLimit'] = response3.json().get('limit',0)

    response4 = session.get('https://lk.megafon.ru/api/profile/name')
    if response4.status_code == 200 and 'json' in response4.headers.get('content-type'):
        result['UserName'] = response4.json()['name']

    response5 = session.get('https://lk.megafon.ru/api/tariff/current')
    if response5.status_code == 200 and 'json' in response5.headers.get('content-type'):
        result['TarifPlan'] = response5.json().get('name','')

    response6 = session.get('https://lk.megafon.ru/api/lk/mini/options')
    if response6.status_code == 200 and 'json' in response6.headers.get('content-type'):
        servicesDto = response6.json().get('servicesDto',{})
        result['UslugiOn'] = f"{servicesDto.get('free','')}/{servicesDto.get('paid','')}"

    response7 = session.get('https://lk.megafon.ru/api/options/remaindersMini')
    if response7.status_code == 200 and 'json' in response7.headers.get('content-type'):    
        response7.json().get('remainders',{})
        remainders = response7.json().get('remainders',[{}])[0].get('remainders',[])
        minutes = [i['availableValue'] for i in remainders if i['unit']=='мин']
        if len(minutes)>0: 
            result['Min'] = sum([i['value'] for i in minutes])
        internet = [i['availableValue'] for i in remainders if i['unit'] in ('ГБ','МБ')]
        unitDiv = settings.UNIT.get(interUnit,1)
        if len(internet)>0: 
            result['Internet'] = sum([round(i['value']*settings.UNIT.get(i['unit'],1)/unitDiv,3) for i in internet])
        sms = [i['availableValue'] for i in remainders if i['unit'].startswith('шту')]
        if len(sms)>0: 
            result['SMS'] = sum([i['value'] for i in sms])

    store.save_session(storename, session)
    return result

if __name__ == '__main__':
    print('This is module megafon')