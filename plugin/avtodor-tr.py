# -*- coding: utf8 -*-
''' Автор ArtyLa '''
import os, sys, re, logging
import requests
import store

# Строка для поиска баланса ФИО и лицевого счета на странице
re_balance = r'(?usi)<td>Баланс</td>.*?<td>(.*?)<'
re_userName = r'(?usi)<td>Клиент ?</td>.*?<td>(.*?)<'  
re_licSchet = r'(?usi)<td>Лицевой счет</td>.*?<td>(.*?)<'  

icon = '789CED92DD4B936118C67F417F407F826E53A3830812EB2C282283A213AB83E82084223B089122D3AC24A3843E44A31A940C2953D230842888547469F32B9D5F5B664D74CEE9F6EEF3FDDADEF56C8DD161D069375C3C07F7733DD7755FF7B3FF68C956325522B05D605B165BC8FBDDC8F6FFACD4FFE25F30B7F003BBC34528A26018062BDE0DEC632E3E8FBB33B04FB80886E399DED8CC128E2937BAAEE7F807CA5D1495AD70F161102D61B0BCA1B1B7DA4751D53A85D57E0AEBFC58ED32492345A94D6257F32ADF3D2B18597EC59D0096135E2CA7D768EA8992481AF48E2B14556F62AE0D60BA19E090354C5C33A8FC2093F73842C7C07C4EBF77284EC1A9352C677C149C5FA7E65598B09CE4ED57959DB783986E05C96F94681C9219F526287816A1BC7D1643E8A4F991B841F185752C677D98C569AEF473F881C4805BC5E9D5296B8B907F3F84F95118EBA44A8B78B7D8B68ACFE7CFF08D9481C3A552D51A62B798D77C49F8AE1133D507A9E88E31ECD16977AA9476C4303D8F503BACF064466560D295E5A790E249167D0936A3493ECEA95CEF8D51FA34CC0EA16B690A71A43346CB84C6CB058D6B0E95F241056B9F33C78F2906FBEA031CBC17A4AA2B4AEB88C2E092CEF86A8277DF749AC784BF7E99E3EF654E7E92A91C55A9EBF72049526E0F973BA398AF6E62BA21326F9032999985F61E5B94633D31CEF5C95CF9A2D230A572774EA3CEA93032BD90DBC37220C99B49856E914FD7B4CAEB198DCE5981799D0E9746BB5BE4B0A8F342F86AFB99C0E649E05C0BE5F8691FE93FF6D77FD748DF4FF10B3797CA66'

def get_balance(login, password, storename=None):
    logging.info(f'start get_balance {login}')
    result = {}
    url = 'https://avtodor-tr.ru/account/login'
    session = store.load_or_create_session(storename)
    response1 = session.get(url)
    if re.search(re_balance, response1.text):
        logging.info(f'Already logoned {login}')
    else:
        # Логинимся
        logging.info(f'relogon {login}')
        session = store.drop_and_create_session(storename)
        # https://stackoverflow.com/questions/12385179/how-to-send-a-multipart-form-data-with-requests-in-python
        files = {"email": (None,login), "password": (None,password), "submit0": (None,'Подождите...'), "return_url": (None,''),}
        response1 = session.post(url, files=files)
        if response1.status_code != 200:
            raise RuntimeError(f'POST Login page {url} error: status_code {response1.status_code}')
    bal = re.search(re_balance, response1.text).group(1).replace(',', '.').strip()
    result['Balance'] = re.sub(r'(?usi)[^\d.,]', '', bal)
    
    try:
        result['userName'] = re.search(re_userName, response1.text).group(1).replace('&nbsp;', '').strip()
    except Exception:
        logging.info(f'Not found userName')
    try:
        result['licSchet'] =  re.search(re_licSchet, response1.text).group(1).replace('&nbsp;', '').strip()
    except Exception:
        logging.info(f'Not found licSchet')
    
    store.save_session(storename, session)
    return result


if __name__ == '__main__':
    print('This is module avtodor-tr')
