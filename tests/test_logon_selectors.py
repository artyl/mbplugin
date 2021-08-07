import pytest, importlib
import conftest  # type: ignore # ignore import error
from playwright.sync_api import sync_playwright
import store, browsercontroller

def check_logon_selectors(page, login_url, user_selectors):
    ''' Этот метод для тестирования, поэтому здесь можно assert
    Проверяем что селекторы на долго не выполняются - это максимум того что мы можем проверить без ввода логина и пароля
    '''
    page.goto('about:blank')
    selectors = browsercontroller.default_logon_selectors.copy()
    assert set(user_selectors)-set(selectors) == set(), f'Не все ключи из user_selectors есть в selectors. Возможна опечатка, проверьте {set(user_selectors)-set(selectors)}'
    selectors.update(user_selectors)
    # TODO fix for submit_js -> chk_submit_js
    selectors['chk_submit_js'] = selectors['submit_js'].replace('.click()','!== null')
    print(f'login_url={login_url}')
    page.goto(login_url)
    page.evaluate(selectors['before_login_js'])
    page.wait_for_selector(selectors['password_selector'])
    for sel in ['chk_login_page_js', 'login_clear_js', 'password_clear_js', 'chk_submit_js']:
        if selectors[sel] !='':
            print(f'Check {selectors[sel]}')
            eval_res = page.evaluate(selectors[sel])
            if sel.startswith('chk_'):
                assert eval_res == True , f'Bad result for js:{sel}:{selectors[sel]}'
            else:
                assert eval_res == '' , f'Bad result for js:{sel}:{selectors[sel]}'
    for sel in ['login_selector', 'password_selector', 'submit_selector']:
        if selectors[sel] !='':
            print(f'Check {selectors[sel]}')
            assert page.evaluate(f"document.querySelector('{selectors['login_selector']}') !== null")==True, f'Not found on page:{sel}:{selectors[sel]}'


@pytest.mark.slow
def test_logon_selectors():
    #print(f'login_url={a1by.login_url}')
    #self = a1by.browserengine('test', 'test', 'test', login_url=a1by.login_url, user_selectors=a1by.user_selectors)
    #self.main('check_logon')
    with sync_playwright() as sync_pw:
        browser = sync_pw.chromium.launch_persistent_context(
            user_data_dir=store.abspath_join(store.options('storefolder'), 'headless', 'test'),
            headless=False,
        )
        page = browser.pages[0]
        [p.close() for p in browser.pages[1:]]
        # TODO add parking_mos rostelecom
        plugins = 'a1by,beeline_uz,lovit,megafonb2b,mosenergosbyt,mts,onlime,test3,uminet,vscale,yota'.split(',')
        for plugin in plugins:
            module = __import__(plugin, globals(), locals(), [], 0)
            importlib.reload(module)  # обновляем модуль, на случай если он менялся            
            print(f'plugin={plugin}, login_url={module.login_url}')
            check_logon_selectors(page, login_url=module.login_url, user_selectors=module.user_selectors)
