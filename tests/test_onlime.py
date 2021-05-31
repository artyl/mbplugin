import pytest
import conftest
import onlime  # pylint: disable=import-error

# Игнорирование RuntimeWarning пришлось включить из-за того что pytest думает что нужен await в 
# self.browser.on("disconnected", self.disconnected_worker)
# и ругается - RuntimeWarning: coroutine ..... was never awaited
@pytest.mark.filterwarnings('ignore::RuntimeWarning')
@pytest.mark.slow
def test_onlime_logon_selectors():
    print(f'login_url={onlime.login_url}')
    self = onlime.browserengine('test', 'test', 'test', login_url=onlime.login_url, user_selectors=onlime.user_selectors)
    self.main('check_logon')
