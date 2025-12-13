#!/usr/bin/python3
# -*- coding: utf8 -*-
import os, sys, re, time, logging, collections
import browsercontroller, store

icon = '789c85533d685441103ec140849c6f673d0b45482ab5b230106bc54e520411244840fc4525625a8b07c9db9dddf7ee475021d7893ff8d388a6b04861fc0563633a3b5110150d09686202f15ebe79897017ee928561879df966bef9d943bd3d9b73d9e981ec85a855d994eb5a31c0fe7aeb8ab43a61b86da763bae9ad9a7386969c518b3153ea2dbdf02638d81a99cb5538e88a2dbd84ff3f609f78a3af0077de59554e98bee17d3a36d4df0c5b2aedda02cc187ce699d565602e411f4b1c8d838be7481f45ac298991d8fc81b5f838d27db0a79ec97a43b6e8c1c1d234f44fe59852e813887f1cf819c7c1ed34455bea0eeaac22cf7736ea04e2cc94132d983b90a112f02212d719fd007e5fa2a8b0a31e8fb787b03f478e73c203f96ba8bf04de7d31abb92c1eab67d20be4fa131bb5af114ff780ff00fea7b33a0ccdfaa8b03fb319357ead04bca1bbb0dd107ed6e67737f08ff4d56c5e23fa24e2bf2d7a2d31ae3bab0771ff42dd7f6347fdc0be837d52fadd907f38bf07b5fe401d6f9ca323f09f802c814f2d71fab3b3c110630e98478a1e5d6c3643e43f03df1a72bcc20c07a09f42bc0be8c131e12d9c90fb51186eef6886670e486a438f16116b01f747709aca7ac1b4e0598d168b1d85665839954aa090ef37f6f49670817e5f764af667a3dd9523bcc0ef2b76b8fcffad7e4fc2305061d8d9de0a5fad76b701ff5efe4af56c775b436d911e903a78441f5e8f4362d5a0f418319ec27f3813ab46f1368b5a26319b60fd1a3adbd13383d9fd947fbbfa77e7713f9619aff55f06776b2594'

login_url = 'https://rucaptcha.com/enterpage'

class browserengine(browsercontroller.BrowserController):
    def data_collector(self):
        self.page_goto(login_url)
        self.sleep(1)
        state = []
        for step in range(1,3):
            # balance, password
            state = self.page_evaluate('[document.querySelector("div#finances")!=null, document.querySelector("input[type=password]")!=null]')
            if any(state): 
                break
        if state == [False, True]:
            logging.error('Не осуществлен вход в ЛК')
            return None
        elif state == [False, False]:
            logging.error('Неизвестное состояние страницы ЛК')
            return None
        self.result['Balance'] = round(self.page_evaluate('initialGlobalState.globalApi.queries["getDashboard(undefined)"].data.balance.amount'),2)

def get_balance(login, password, storename=None, **kwargs):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    store.update_settings(kwargs)
    store.turn_logging()
    return browserengine(login, password, storename, plugin_name=__name__).main()


if __name__ == '__main__':
    print('This is module uminet')
