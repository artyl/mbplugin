# -*- coding: utf8 -*-
''' Автор ArtyLa '''
import os, sys, re, logging
import store, settings

icon = '789C73F235636100033320D600620128666450804840E591C1FFFFFFA98E3FBC7ECA706CCB6C86E53D290CCBBB9319564FCC6638BF7F25C3AF9FDF09EA3DB2713A43758008434F9A31C3A619650C7B977732ACEC4D67688BD760688E5262B87E6A274EBDDBE6D5313446C8335C3FBD0343EECF9F5F0CBB97B63154F8F0339C3FB00A43FEF685030C659E3C0C8F6E9C06F3FFFEFDC3F0E7F72F0C75C7B7CE6588099AC9F0EEDD3F14F1F90DA10C1BA617C3F99FDEBD60985EEA0E0E0B6475FFFEFD6748CBFBCC306B01222CBE7E7ACB50E6C5CBF0F4EE2514B5170EAC66E84CD265B87BF1108AF8BACD3F1962523FC1F90FAF9F62A8F217069AFD17C3BD2F1E5C63E8CD300187E3FF7F1037DFB8F587C1D9EF03C3AF5F1035203F57FA0962F5EF87D74F182617D8336C98560C0E1390D8F59B7F185CFC11FABF7D7AC7500E74FFA39B6750F4DE3ABF8FA133598FE1D2E17528E26B37FD64884DFB8422B6B0399261DD940238FFF3FB570C1372AC185E3CBC86117EC9399F18E62FFD8122FEECDE657018DC01C62338BE817EF9F9FD0B867FF6AFEA65C808AB6378FFE11F86DC1E6018D58548315C38B806C84795FFF3FB27C3B6F975E0B479E3CC2E9C69F0E4F6790C75A1D20C5D29FA0C9B6757311C5A3F8561FDB42270DA6D8D53677870F538C13CF0FDCB0786D3BB16312C698B659855E5CBB0069C7F5681DD40EDBC0A00F3E78F1E'

login_url = 'http://strelkacard.ru'

def get_card_info(cardnum):
    # чтобы не ругался на ошибки сертификатов
    baseurl = 'http://strelkacard.ru'
    # Если не поменять user-agent - не отдаст
    user_agent = store.options('user_agent', pkey=store.get_pkey(login=cardnum, plugin_name=__name__))
    if user_agent.strip() == '':
        user_agent = settings.default_user_agent
    url = f'https://strelkacard.ru/api/cards/status/?cardnum={cardnum}&cardtypeid=3ae427a1-0f17-4524-acb1-a3f50090a8f3'
    session = store.Session(storename=None, headers={'User-Agent': user_agent, 'Referer': baseurl + '/'})
    session.disable_warnings()  # pylint: disable=no-member
    response = session.get(url, verify=False)
    res =  response.json()
    return res


def get_balance(login, password, storename=None, **kwargs):
    result = {}
    card_info = get_card_info(login)
    result['Balance'] = card_info['balance']/100.
    if card_info.get('emergencyblocked', False):
        result['BlockStatus'] = 'Emergency Blocked'
    if card_info.get('cardblocked', False):
        result['BlockStatus'] = 'Card Blocked'
    return result


if __name__ == '__main__':
    print('This is module strelka')
