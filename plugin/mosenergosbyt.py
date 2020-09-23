#!/usr/bin/python3
# -*- coding: utf8 -*-
import asyncio, time, re, json, subprocess, logging, shutil, os, sys, traceback
import urllib
import pyppeteer  # PYthon puPPETEER
#import pprint; pp = pprint.PrettyPrinter(indent=4).pprint
import store, settings
import pyppeteeradd as pa

icon = '789c73f235636600033320d600620128666490804800e58ff041300cfc270b6cdc7868ca94ddab56edbe73e7fe9b376fbe7dfbf6ffffbfffffffe050feb7b0f0a4b0f00d46c663f6f6b3d7ae5d76e8e0be1933d6a4a71f6e6db9f8f1e3574c0d9b363fd0d179cec7f7c9d0f0cea74f3f7ffefc9e9aba8681e1aab4f4e5f7efbf61aa7ffbf68bb3f3556dedff7c7c5f8d8ceeb9b9df97963ec3c0f03839f921d861589c545171c5d4ec9b98d87f2eeeb79c5c4f98989f31333f5ebaf439d0b28f1f3ffefefd1b4dc3b66d0fcccc9ec8c9ff4f4a7ed3da7a9895f59c84e4e3a74fbfb7b6362b28286cddba154dfdebd79f6c6d2fe8e9ffb7b27e1f11b18299e58e97d7a37ffffe6766663033332f5bb60c5b285d56d7fc262bff5944643913f393cecee740d1c2c2422121a1952b5762fa61cb9687d2324fb474fe494bbfe3e37f72f0e0cbe7cf9f151515aaa8a8ac59b30653fdbb779f7574af2a2aff5756fd6f6cf2ece1c31701017e76b6b67676766bd7aec51a4a25a55784843f2928fdacaa7afefdfb97acac2c3737773f3f7f1ceaff7ffaf463dfbe77376e7cf9f1039418debe7d5b5e5eeee7e7b77af56aacea31c1cd9b3767cf9e7dedda3522d5530800550a6598'

class mosenergosbyt_over_puppeteer(pa.balance_over_puppeteer):
    async def async_main(self):
        await self.do_logon(
            url='https://my.mosenergosbyt.ru/auth',
            user_selectors={
                #'before_login_js':"document.querySelector('div[data-tab=login]').click()", # Сначала кликаем по Логин
                'chk_lk_page_js': "document.querySelector('#authPage')!=null",  # Признак того что залогинились (на сложных страница лучше не оставлять по паролю а искать специфичный тэг)
                'remember_checker': "document.querySelector('form input[name=remember]').checked==false",  
                #'remember_js': "document.querySelector('form input[name=remember]').click()",
                'remember_selector': "form input[name=remember]",
                })
        # Сначала из файла gate_lkcomu?action=sql&query=LSList& получаем id_service по номеру лицевого счета
        res1 = await self.wait_params(params=[{
            'name': 'id_service',
            'url_tag': ['gate_lkcomu?action=sql&query=LSList&'],
            'jsformula': f'data.data.filter(s => s.nn_ls=="{self.acc_num}")[0].id_service',
        },{
            'name': 'vl_provider',
            'url_tag': ['gate_lkcomu?action=sql&query=LSList&'],
            'jsformula': f'data.data.filter(s => s.nn_ls=="{self.acc_num}")[0].vl_provider',
        }], save_to_result=False)  # Это промежуточные данные их не берем в результат
        id_service = res1['id_service']  #   Нам нужен id_service
        vl_provider = res1['vl_provider']  # и vl_provider чтобы искать остальные данные
        if id_service is None or vl_provider is None:
            logging.error(f'Не найден лицевой счет')
            raise RuntimeError(f'Не найден лицевой счет')
        # Теперь получаем данные по лицевому счету
        res1 = await self.wait_params(params=[{
            'name': 'Balance',
            'url_tag': ['gate_lkcomu?action=sql&query=smorodinaTransProxy&', 'AbonentCurrentBalance', urllib.parse.quote(vl_provider)],
            'jsformula': f'_.sum(data.data.map(s => s.sm_balance))',
        }], url=f'https://my.mosenergosbyt.ru/accounts/{id_service}',  # Соберем после захода на эту страницу
        )
        
            

def get_balance(login, password, storename=None):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    return mosenergosbyt_over_puppeteer(login, password, storename).main()


if __name__ == '__main__':
    print('This is module mosenergosbyt on puppeteer')
