# -*- coding: utf8 -*-
''' Автор ArtyLa '''
import os, sys, re, logging
import requests
import store

re_balance = r'(?usi)Баланс.*?>.*?>(\d*\.\d*)<'

icon = '789CB593CF4B146118C7BF61EECA2E9520DE749D50B6221044F1E0316F46467419B6123D7AA808245AEB9CE40F9A43DD0A5BC543212E1E36F1DA22F80FA46C58EDE4CECE3B3BBBCEACBBADEBCEAFDE7933117688A07AE07B795F3E3CDFF7FBBCCF956BFDA7C1AA9FEA2255F3914E81FB7971747FB21CC7F91B39FF9AAFD56C7C48963033933BD6DB771A0CC3FE2D6FDB0E24C9C0E868067D7D3B686AFA782CEE7C0A6363192C2F17619AB627AFEB16464624F8FC5B18BE2E627E5E432CA66161414334AAC0E7DB4277F7676C6E56EAF86AD506CF4B6869F984E7828AD9D9021E5246560C58968344A24C7DA4E0F7A7B0B2B25FC71362A0B757C4C0C02EF5E7401034F0912CC46F356C6C1CA0ADED0BCE9CDDC1F4F45E9D7FF7DD8FA22ADADBD3C8E54C762E083AF85B04AF5E17C17122425C1A2F5EEA9EF9B9FE22911CF52E9EE08BE06F2B085FD8452098C6DD072A0E0FBDF377FB3F7EA22114CA40967FF1FB88DC51F1744A47579784ABC30ADEAF5758165EF3DBDE36D0D343E8ECF65896825062FCD7B481A5A5EFE8E89071E932C19B5885FD0FAFFC8786F238D72C63EA5909737325DCBBAF412626F3BDB858A1D9CB686D25585BAB7ACE3F9BB5D0D9A9A2B191607C5CA76FB190CF5B28142CACAE56110810048304F1B837EFCA6506073584C379BA590A5343834267A3E2C64D0D89F5833FDA9F64B286898932D3E4641971DADF30FFCFFEFD00C3708362'

def get_balance(login, password, storename=None):
    logging.info(f'start get_balance {login}')
    result = {}
    session = store.load_or_create_session(storename)
    # Проверяем залогинены ли ?
    response3 = session.get('https://my.cardtel.ru/home')
    if len(re.findall(re_balance, response3.content.decode('utf8'))) > 0:
        logging.info('Old session is ok')
    else:  # Нет, логинимся
        data = {'op': 'auth', 'login': login, 'pwd': password, 'red': '1', 'remember': 'false'}
        session = store.drop_and_create_session(storename)
        response2 = session.post('https://my.cardtel.ru/process', data=data)
        if response3.status_code != 200:
            raise RuntimeError(
                f'Login error: status_code {response2.status_code}!=200')
        response3 = session.get('https://my.cardtel.ru/home')
        if response3.status_code != 200:
            raise RuntimeError(
                f'Get balance page error: status_code {response2.status_code}!=200')
    balance = re.findall(re_balance, response3.content.decode('utf8'))
    if len(balance) == 0:
        raise RuntimeError(f'Balance not found on page')
    result['Balance'] = balance[0]
    store.save_session(storename, session)
    return result


if __name__ == '__main__':
    print('This is module cardtel')
