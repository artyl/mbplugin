#!/usr/bin/python3
# -*- coding: utf8 -*-
import collections, hashlib, json, pathlib
import bs4
import browsercontroller, store, settings, logging

State = collections.namedtuple('State', 'url, active, selection', defaults=('', '', ''))

class browserengine(browsercontroller.BrowserController):
    def active_element(self):
        return self.page_evaluate('document.activeElement==document.body?"":document.activeElement.outerHTML')
    
    def selection(self):
        return self.page_evaluate('window.getSelection().type=="None"?"":((()=>{c=window.getSelection().getRangeAt(0);a1=c.startContainer.parentElement.outerHTML;a2=c.endContainer.parentElement.outerHTML; return a1==a2?a1:a1+a2})())')

    def discovery_write(self, descr, data, is_html=False, is_json=False):
        with self.discovery_log.open(mode='a', encoding='utf8') as f:
            if isinstance(data, str) and is_html:
                data = bs4.BeautifulSoup(data, 'html.parser').prettify()
            if isinstance(data, str) and is_json:
                data = json.dumps(json.loads(data), ensure_ascii=False)
            if not isinstance(data, str) and is_json:
                data = json.dumps(data, ensure_ascii=False)
            f.write(f'{descr}:{data}\n\n')

    def data_collector(self):
        logging.info(f'Start discovery')
        self.discovery_log = pathlib.Path(store.abspath_join(self.options('loggingfolder'), self.storename + '.discovery.log'))
        if self.discovery_log.exists():
             self.discovery_log.unlink()
        states: list[State] = [State()]
        prev_responses = set()  # all saved responses
        while not self.page.is_closed():
            state1 = states[-1]
            state2 = State(self.page.url, self.active_element(), self.selection())
            new_responses = set(self.responses).difference(prev_responses)
            for el in new_responses:
                self.discovery_write('CATCH', el)
            prev_responses = set(self.responses)
            if state1 == state2:
                self.sleep(0.1)  # no change
                continue
            states.append(state2)
            # ss = self.page.screenshot() # hashlib.md5(b'aa').hexdigest()
            # breakpoint()
            path = self.page_screenshot()
            self.discovery_write('SCREENSHOT', path)
            if state1.url == state2.url and state1.active == state2.active and state1.selection.startswith(state2.selection):
                self.sleep(0.2)  # no change
                continue
            if state1.url != state2.url:
                self.discovery_write('URL', state2.url)
                continue
            if state1.active != state2.active:
                self.discovery_write('ACTIVE', state2.active)
                continue
            if state1.selection != state2.selection:
                self.discovery_write('SELECTION', state2.active)
                continue
            # breakpoint()
        self.discovery_write('CLOSE', '')
        self.result['Balance'] = 54321  # Заглушка чтобы не было ошибки


def get_balance(login, password, storename=None, **kwargs):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    store.update_settings(kwargs)
    store.turn_logging()
    return browserengine(login, password, storename, plugin_name=__name__).main()


if __name__ == '__main__':
    print('This is module for discovery site')
