import pytest, importlib, traceback, os, sys, shutil, time
import conftest  # type: ignore # ignore import error
from playwright.sync_api import sync_playwright
import store, browsercontroller

def page_evaluate(page, eval_string, default=None, args=[]):
    ''' page_evaluate из browsercontroller '''
    try:
        return page.evaluate(eval_string, args)
    except Exception:
        exception_text = ''.join(traceback.format_exception(*sys.exc_info()))
        if 'Execution context was destroyed' not in exception_text:
            raise

def check_logon_selectors(page, login_url, user_selectors):
    ''' Этот метод для тестирования, поэтому здесь можно assert
    Проверяем что селекторы на долго не выполняются - это максимум того что мы можем проверить без ввода логина и пароля
    '''
    selectors = browsercontroller.default_logon_selectors.copy()
    assert set(user_selectors)-set(selectors) == set(), f'Не все ключи из user_selectors есть в selectors. Возможна опечатка, проверьте {set(user_selectors)-set(selectors)}'
    selectors.update(user_selectors)
    # TODO fix for submit_js -> chk_submit_js
    selectors['chk_submit_js'] = selectors['submit_js'].replace('.click()','!== null')
    print(f'login_url={login_url}')
    if login_url is not None:
        page.goto(login_url)
    for _ in range(30):
        if page_evaluate(page,selectors['chk_login_page_js']):
            break
        page.wait_for_timeout(1000)
    page_evaluate(page,selectors['before_login_js'])
    sel = 'chk_submit_after_login_js'
    selector_checklist = ['chk_login_page_js', 'login_clear_js', 'chk_submit_js', 'chk_lk_page_js']
    # Для сайтов с раздельным вводом логина и пароля не можем проверить наличие поля пароля
    if selectors[sel] != '':
        assert page_evaluate(page,selectors[sel]) == True, 'Bad result (False) for {sel}'
    else:
        page.wait_for_selector(selectors['password_selector'])
        selector_checklist.extend(['password_clear_js'])
    for sel in selector_checklist:
        if selectors[sel] !='':
            eval_res = page_evaluate(page,selectors[sel])
            if sel.startswith('chk_lk_page_js'):
                assert eval_res == False , f'Bad result for js:{sel}:{selectors[sel]} must be False'
            elif sel.startswith('chk_'):
                assert eval_res == True , f'Bad result for js:{sel}:{selectors[sel]} must be True'
            else:
                assert eval_res == '' , f'Bad result for js:{sel}:{selectors[sel]} must be ""'
    for sel in ['login_selector', 'password_selector', 'submit_selector']:
        if selectors[sel] !='':
            assert page_evaluate(page,f"document.querySelector('{selectors['login_selector']}') !== null")==True, f'Not found on page:{sel}:{selectors[sel]}'

# plugins = 'parking_mos,rostelecom,a1by,beeline_uz,lovit,megafonb2b,mosenergosbyt,mts,onlime,test3,uminet,vscale,yota'.split(',')
# "    def test_rostelecom(self):\n        plugin = 'rostelecom'\n        self.do_test_plugin(plugin)"
# print('\n\n'.join([s.replace('rostelecom',i) for i in plugins]))
@pytest.mark.slow
class TestUM:
    def setup_class(self):
        print ("class setup")
        self.sync_pw = sync_playwright().start()
        self.user_data_dir = store.abspath_join(store.options('storefolder'), 'headless', 'test')
        # Firefox в некоторых версиях не хочет стартовать если не создана папка профиля
        if not os.path.exists(self.user_data_dir):
            os.makedirs(self.user_data_dir, exist_ok=True)
        self.browser = self.sync_pw.firefox.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            # Если нужно показать браузер
            # SET HEADLESS_CHROME=False
            headless=os.environ.get('HEADLESS_CHROME','True').lower()=='true',
        )
        self.page = self.browser.pages[0]
        [p.close() for p in self.browser.pages[1:]]

    def teardown_class(self):
        self.sync_pw.stop()
        time.sleep(2)
        shutil.rmtree(self.user_data_dir, ignore_errors=True)

    def setup_method(self, method):
        self.page.goto('about:blank')

    def teardown_method(self, method):
        self.page.goto('about:blank')

    def do_test_plugin(self, plugin):
        module = __import__(plugin, globals(), locals(), [], 0)
        importlib.reload(module)  # обновляем модуль, на случай если он менялся
        print(f'plugin={plugin}, login_url={module.login_url}')
        check_logon_selectors(self.page, login_url=module.login_url, user_selectors=module.user_selectors)

    def test_parking_mos(self):
        self.page.goto('https://lk.parking.mos.ru/auth/login')
        self.page.evaluate("window.location = '/auth/social/sudir?returnTo=/../cabinet'")
        plugin = 'parking_mos'
        self.do_test_plugin(plugin)

    def test_a1by(self):
        plugin = 'a1by'
        self.do_test_plugin(plugin)

    def test_beeline_uz(self):
        plugin = 'beeline_uz'
        self.do_test_plugin(plugin)

    def test_lovit(self):
        plugin = 'lovit'
        self.do_test_plugin(plugin)

    def test_megafonb2b(self):
        plugin = 'megafonb2b'
        self.do_test_plugin(plugin)

    def test_mosenergosbyt(self):
        plugin = 'mosenergosbyt'
        self.do_test_plugin(plugin)

    def test_mts(self):
        plugin = 'mts'
        self.do_test_plugin(plugin)

    def test_onlime(self):
        plugin = 'onlime'
        self.do_test_plugin(plugin)

    def test_rostelecom(self):
        plugin = 'rostelecom'
        self.do_test_plugin(plugin)

    def test_test3(self):
        plugin = 'test3'
        self.do_test_plugin(plugin)

    def test_uminet(self):
        plugin = 'uminet'
        self.do_test_plugin(plugin)

    def test_vscale(self):
        plugin = 'vscale'
        self.do_test_plugin(plugin)

    def test_yota(self):
        plugin = 'yota'
        self.do_test_plugin(plugin)
