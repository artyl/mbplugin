import os, pytest
import conftest  # type: ignore # ignore import error
import browsercontroller

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
    be_pw.launch_config['headless'] = os.environ.get('HEADLESS_CHROME', 'True').lower() == 'true'
    be_pw.main()
