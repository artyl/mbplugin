import os, pytest
import conftest  # type: ignore # ignore import error
import browsercontroller

class BrowserenginePlaywright(browsercontroller.BalanceOverPlaywright):
    def data_collector(self):
        self.page_goto('https://example.com/')
        print(self.page.url)
        assert self.page.url == 'https://example.com/'
        self.page_click('a')
        print(self.page.url)
        assert self.page.url == 'https://www.iana.org/domains/reserved'

@pytest.mark.skip('Garbage collector produce an exception: ResourceWarning: subprocess is still running')
@pytest.mark.slow
def test_browsercontroller_engine_playwright():
    argv = ['login', 'password', 'test_storename']
    be_pw = BrowserenginePlaywright(*argv)
    be_pw.launch_config['headless'] = os.environ.get('HEADLESS_CHROME', 'True').lower() == 'true'
    be_pw.main()

@pytest.mark.slow
class TestBrowserClass():
    def test_run(self):
        self.argv = ['login', 'password', 'test_storename']
        self.be_pw = BrowserenginePlaywright(*self.argv)
        self.be_pw.launch_config['headless'] = os.environ.get('HEADLESS_CHROME', 'True').lower() == 'true'
        self.be_pw.main()
