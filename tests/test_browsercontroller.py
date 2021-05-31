import time
import pytest
import psutil
import conftest  # pylint: disable=import-error
import browsercontroller
import pyppeteeradd


class browserengine_pyppeteer(pyppeteeradd.BalanceOverPyppeteer):
    def data_collector(self):
        self.page_goto('https://example.com/')
        print(self.page.url)
        assert self.page.url == 'https://example.com/'
        self.page_click('a')
        print(self.page.url)
        assert self.page.url == 'https://www.iana.org/domains/reserved'


class browserengine_playwright(browsercontroller.BalanceOverPlaywright):
    def data_collector(self):
        self.page_goto('https://example.com/')
        print(self.page.url)
        assert self.page.url == 'https://example.com/'
        self.page_click('a')
        print(self.page.url)
        assert self.page.url == 'https://www.iana.org/domains/reserved'


@pytest.mark.slow
def test_browsercontroller_engine_playwright():
    argv = ['login', 'password', 'test_storename']
    be_pw = browserengine_playwright(*argv)
    be_pw.launch_config['headless'] = False
    be_pw.main()


@pytest.mark.slow
def test_browsercontroller_engine_pyppeteer():
    argv = ['login', 'password', 'test_storename']
    be_pp = browserengine_pyppeteer(*argv)
    be_pp.main()
    while len(psutil.Process().children())>2:
        #open('c:\\new\\aaaa','a').write(repr(psutil.Process().children())+'\n\n')
        time.sleep(0.1)

# TODO есть два класса BalanceOverPlaywright и BalanceOverPyppeteer оба наследники класса _BrowserController
# как протестировать оба не переписывая метод data_collector
