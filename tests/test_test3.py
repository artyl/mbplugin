import pytest
import conftest
import test3  # pylint: disable=import-error

# Игнорирование RuntimeWarning пришлось включить из-за того что pytest думает что нужен await в 
# self.browser.on("disconnected", self.disconnected_worker)
# и ругается - RuntimeWarning: coroutine ..... was never awaited
@pytest.mark.filterwarnings('ignore::RuntimeWarning')
@pytest.mark.slow
def test_test3_logon_selectors():
    print(f'login_url={test3.login_url}')
    self = test3.browserengine('test', 'test', 'test', login_url=test3.login_url, user_selectors=test3.user_selectors)
    self.main('check_logon')
