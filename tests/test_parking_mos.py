import pytest
import conftest
import pyppeteeradd as pa  # pylint: disable=import-error
import parking_mos  # pylint: disable=import-error

class balance_over_puppeteer_parking_mos(pa.balance_over_puppeteer):
    async def async_check_logon_selectors_prepare(self):
        await self.page_goto('https://lk.parking.mos.ru/auth/login')
        await self.page_evaluate("window.location = '/auth/social/sudir?returnTo=/../cabinet'")

# Игнорирование RuntimeWarning пришлось включить из-за того что pytest думает что нужен await в 
# self.browser.on("disconnected", self.disconnected_worker)
# и ругается - RuntimeWarning: coroutine ..... was never awaited
@pytest.mark.filterwarnings('ignore::RuntimeWarning')
@pytest.mark.slow
def test_parking_mos_logon_selectors():
    print(f'login_url={parking_mos.login_url}')
    self = balance_over_puppeteer_parking_mos('test', 'test', 'test', login_url=parking_mos.login_url, user_selectors=parking_mos.user_selectors)
    self.main('check_logon')
