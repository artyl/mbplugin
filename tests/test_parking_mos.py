import pytest
import conftest  # type: ignore # ignore import error
import parking_mos  # pylint: disable=import-error

class balance_over_parking_mos(parking_mos.browserengine):
    def check_logon_selectors_prepare(self):
        self.page_goto('https://lk.parking.mos.ru/auth/login')
        self.page_evaluate("window.location = '/auth/social/sudir?returnTo=/../cabinet'")

@pytest.mark.slow
def test_parking_mos_logon_selectors():
    print(f'login_url={parking_mos.login_url}')
    self = balance_over_parking_mos('test', 'test', 'test', login_url=parking_mos.login_url, user_selectors=parking_mos.user_selectors)
    self.main('check_logon')
