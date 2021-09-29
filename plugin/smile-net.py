# -*- coding: utf8 -*-
''' Автор ArtyLa '''
import os, sys, re, logging
import requests
import store

icon = '789C65535B485451145D338E14D9400FEDF5950465D857A51F2104817D14D64720FE0AE547914124D94BA33E82088AE885501452849295669123939A44666ABE98291F33EAD88CD3CC75C6B9CF73EFDCDBBDE7CE1D9C3AB0388F7DCE5E7BAFBDCF81B26207E828D651A0634D0A366C350D29FBF2A1AA2A344D83222B906599AE7949A2B3AAC39388D1B5A66A9088045E346DFF4255931065029E08749F4C4A5014058EF733693B3D574D0E4248FAADC12B4A62863F26266154E742E314DDB7F9199D9FE87E751ED1F4250999B11435F4A2D63D4ED7B6DB9DC877CD22EB75187B87FEC0EEF6D15CD1EE43B5274CFD9871A9945F4AE5BCAABE0DB9F54DD87C73188E973EE02307879B07DE45819639D8DB82293E05449433F8C7621CCA9B0790776718F66911590919CE108B9CB800DB2F05B60F8B381F60E0E564CA6B6860E96FC453D5ED85F35A37567E6691DDD587825397905F79061B8E9FC58A0511F6BE38B2DA99FFB4EF5C60D0C36BB8B114C2A6677EAC0E88D81D65B07362167B222C4A17F5F85BA3B0CFF2B0B70650E5E5F03691AA595246C3D46FD4CCCCE1692282A3A3316CF4131C6C69C6F6D3B5709E38871D9F3AE08CF2C8F6C9703C9A84A3691EDB0682188AB234070346AD6B3C015C082D62DDA0840A57072AC31C0E0FF4A3A4E1210A63BA1E8D5E143DFE66D68EEA6D6A6F6940888893BE200E793894CCB0A86135D4450454300439232CB65C74A1AE770283418EEAA5A67AC7AAA52CC928B8E7C6911F3F513E1F47E97808B95F23587B771879579A917BD985692699D65B55950C1DF7DF77E37A8F1FF302C1BE9E313C89C7706B6901BBBA26F1254250F8C08DF557DFD03EA43ED279987F658413A80E3C51684E2FC209544F05D3FFCA40D9F3EF7835194EEF8D388C37CB7BD0FA1F73B28663FDDE747ED67D7F9CCB38B37AD8F221E83066E3CE885E234B5FE3CCE05AFEF62FCE987AC1'

login_url = 'https://user.smile-net.ru/newpa/?handler=Login'
login_checkers = ['<input[^>]*name="login"[^>]*', '<input[^>]*name="password"[^>]*', '<input[^>]*type="submit"[^>]*']

# regexp для поиска баланса на странице
re_balance = r'(?usi)>Баланс.*?value.*?>\s*(-?\d+[.,]\d+) '
re_expired = r'(?usi)Дата окончания.*?value.*?>\s*(.*?)<'
re_userName = r'(?usi)handler=Customer.*?>(.*?)<'
re_licSchet = r'(?usi)Номер лицевого счета.*?value.*?>\s*(.*?)<'
re_tarifPlan = r'(?usi)Название текущего тарифа.*?value.*?href.*?>\s*(.*?)<'
re_BlockStatus = r'(?usi)>Статус<.*?value.*?>\s*(.*?)<'

def find_by_regexp(text, param, regexp):
    try:
        return {param: re.search(regexp, text).group(1).strip()}
    except Exception:
        logging.info(f'Not found {param}')    
        return {}

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
        data = {'login': login,'password': password,}
        response = session.post(login_url, data=data)
        if response.status_code != 200:
            raise RuntimeError(f'POST Login page {login_url} error: status_code {response.status_code}')

    result['Balance'] = re.search(re_balance, response.text).group(1).replace(',', '.').strip()
    result.update(find_by_regexp(response.text, 'Expired', re_expired))
    result.update(find_by_regexp(response.text, 'UserName', re_userName))
    result.update(find_by_regexp(response.text, 'licSchet', re_licSchet))
    result.update(find_by_regexp(response.text, 'TarifPlan', re_tarifPlan))
    result.update(find_by_regexp(response.text, 'BlockStatus', re_BlockStatus))
   
    session.save_session()
    return result


if __name__ == '__main__':
    print('This is module smile-net')
