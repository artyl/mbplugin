import pytest
import conftest
import rostelecom  # pylint: disable=import-error


# Игнорирование RuntimeWarning пришлось включить из-за того что pytest думает что нужен await в 
# self.browser.on("disconnected", self.disconnected_worker)
# и ругается - RuntimeWarning: coroutine ..... was never awaited
@pytest.mark.filterwarnings('ignore::RuntimeWarning')
@pytest.mark.slow
def test_rostelecom_logon_selectors():
    print(f'login_url={rostelecom.login_url}')
    self = rostelecom.browserengine('test', 'test', 'test', login_url=rostelecom.login_url, user_selectors=rostelecom.user_selectors)
    self.main('check_logon')
