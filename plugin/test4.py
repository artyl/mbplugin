#!/usr/bin/python3
# -*- coding: utf8 -*-
''' пример плагина почти на чистом playwright без упрощенной логики '''
import time, re, json, logging, os
import browsercontroller

class browserengine(browsercontroller.BrowserController):
    def data_collector(self):
        # Нажмите кнопку "Демо-доступ" или введите логин demo@saures.ru и пароль demo вручную. 
        self.page_goto('https://lk.saures.ru/dashboard')
        self.page_wait_for(expression="document.getElementById('main-wrapper')!=null || document.querySelector('form button[type=submit]')!=null")
        if self.page_evaluate("document.getElementById('main-wrapper')!=null"):
            logging.info(f'Already login')
        elif self.page_evaluate("document.querySelector('form button[type=submit]')!=null"):
            logging.info(f'Login')
            self.page_type("form input[type=text]", self.login)
            self.page_type("form input[type=password]", self.password)
            self.sleep(1)
            self.page_evaluate("document.querySelector('form button[type=submit]').click()")
        else:
            logging.error(f'Unknown state')
            raise RuntimeError(f'Unknown state')
        # Ждем появления информации
        selector = '.page-content .text-dark'
        self.page_wait_for(selector=selector)
        if self.page_evaluate("document.querySelector('.page-content .text-dark')!=null"):
            baltext = self.page_evaluate("document.querySelector('.page-content .text-dark').innerText")
            baltext = re.sub(r'[^\d|,|.-]','',baltext).replace(',', '.')
            self.result['Balance'] = float(baltext)
        else:
            logging.error(f'Not found BALANCE')
            raise RuntimeError(f'Not found BALANCE')
        logging.debug(f'Data ready {self.result.keys()}')
        # Обратите внимание, что возвращать результат нужно сохранив его в self.result

def get_balance(login, password, storename=None):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    return browserengine(login, password, storename, plugin_name=__name__).main()

if __name__ == '__main__':
    print('This is module test3 for test chrome on playwright')
