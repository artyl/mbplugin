# -*- coding: utf8 -*-
''' Автор Pasha '''
''' проверка баланса Mango Office https://www.mango-office.ru/ '''
import os, sys, re, logging
import requests
import store

icon = '789c5d936f4c5b551c866b629aeccb62624c8c31c644330daddb22d2f53fbdbddcdb7b439c7106bf384d16659aa9fb1337956846e234e86414904e706e336c1dc3125a281436a8c028d5398b7143e868279b71c496b4f7b6bd5d7b4bdbd7a3b8c5799227e7c339cffbfb9d9373accf6aee55fc3334842709f7fdcb3d8a47d716c87a60fd1ab707803b0c85a38a9aa6ef54a63db3ad865722617d4dbca0552724edd389392d9568d5bc9e54534d82a26759becbfb9be6905769ed3cd961393c503237fc00e3ae300c7571e84c09e8e804b4db083b9225cdfe64e7e317d2eb8e8472775c67f49c92ed6d18ab39d10e6bdb59580e4dc3b4ef1a8cf571e8b726a07f8164ec4842bb5b80e6a08067eca2ffb1405a792a5150880549c10dbeecb0b97683397e8cf85e981b2fc1f44e14c6376230bc9a806127e1ed24f4ef938c2601555d22367b320ef5aca43838dba2e6dc2f156dbdef82ed6e07ddd50fca1e44f5c71198f6aec0f85612c63d840349181a05e89a45688ea7b071582a3ef293a4de3a526be73ccfc3e6da0bf6740be8632e506d33b01c5984e59318ccef25616e48c27488f8cdc47788d091fa9b46253c352eb5f2de2d0b9ce745d8fa487da7038cb307f489695047af826a8da1fa2381f422c0fc9900639b0843771a1a671a9bc6246c0866e7786fa5cc0fd2e03cf560fb3e05d37306f43717407585417df127e94580a583641c25195f8b3076a7a0ef49a3d2274115c866f821bdcc7b9f033740faef6f07f3ad1bf4a98bb09e8cc0fa551c54a708ea741ad6332954bb32307a24547925a883793c18c9cbbccfbcc00fd7821f7a13b6c1cfc10e9c05e39e06ddb3487262a8e94b8172676075a56021b37efc16f4be2c9ef845c603370a0b7593afd9f9913af023fbc0f9ec60875d60bd01d47816891b07e34b811e253e396ff544167a5277f3ac8c0d5764dc7f73d5de7b33a8e246b7156de777821bff10ecf97eb07e0f187f04cc38f1fdc49fc8809acac214cc4177298f8d97653cfc47b1f8d0f2aaaa4cde5f5de0030733b11fdca41db62927d89951b053d7c04eae80994a830e91dadf1337bc8a2d9155a87e2f42912a777c29afbddf583ea5ac9d6e1c63671c602ff682094d80fdf137421cec7c0ad6ab5950e11c0cd102aaae17b13e5df6d7e7a0fcefff59ce09caed979d1d6cc85d627e0d8259fc19b639e2df20f7b69c4375348f4aa154aa48953b0fcb58f7ffff779bbec452c5f6a52b2dfcf5f9056e299e6757c43c9d90e639516e3970ab5c2196efdeff17dff5a937'

login_url = 'https://auth.mango-office.ru/auth/vpbx'
login_checkers = ['<input[^>]*name="email"[^>]*', '<input[^>]*name="password"[^>]*']

# Строки для поиска баланса и prod_id на странице
re_balance = r'(?usi)info-value">(.*?)</div'
re_prod_id = r'(?usi)data-product-id="(.*?)"'

def get_balance(login, password, storename=None, **kwargs):
    logging.info(f'start get_balance {login}')
    result = {}
    session = store.Session(storename)
    response = session.get(login_url)
    if re.search(re_balance, response.text):
        logging.info(f'Already logoned {login}')
    else:
        # Логинимся
        logging.info(f'relogon {login}')
        session.drop_and_create()
        data = {'app': 'ics','startSession': '1','username': login,'password': password,}
        response = session.post(login_url, data=data)
        if response.status_code != 200:
            raise RuntimeError(f'POST Login page {login_url} error: status_code {response.status_code}')

    # Получаем необходимые значения
    auth_token = response.json().get('auth_token', '')
    refresh_token = response.json().get('refresh_token', '')
    account_id = response.json().get('account_id', '')
    # Заходим в ЛК и получаем prod_id
    data = {'auth_token': auth_token,'refresh_token': refresh_token,'username': login,'app': 'ics','request-uri': '/',}
    response1 = session.post('https://lk.mango-office.ru/auth/create-session', data=data)
    response2 = session.post('https://lk.mango-office.ru/')
    prod_id = re.search(re_prod_id, response2.text).group(1).replace('\'', '')
    # Обновляем токен
    data = {'auth_token': auth_token,'refresh_token': refresh_token}
    response3 = session.post('https://lk.mango-office.ru/' + str(account_id) + '/' + str(prod_id) + '/auth/refresh-token', data=data)
    auth_token = response3.json().get('auth_token', '')
    # Запрашиваем баланс
    data = {'app': 'ics','auth_token': auth_token,'prod_id': prod_id}
    response4 = session.post('https://api-header.mango-office.ru/api/header', data=data)
    data = response4.json()
    balance = data.get('data',[])
    result['Balance'] = balance['account']['fxbalance']

    session.save_session()
    return result

if __name__ == '__main__':
    print('This is module mangooffice')
