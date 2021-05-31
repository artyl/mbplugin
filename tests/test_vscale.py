import pytest
import conftest
import vscale  # pylint: disable=import-error

# Игнорирование RuntimeWarning пришлось включить из-за того что pytest думает что нужен await в 
# self.browser.on("disconnected", self.disconnected_worker)
# и ругается - RuntimeWarning: coroutine ..... was never awaited
@pytest.mark.filterwarnings('ignore::RuntimeWarning')
@pytest.mark.slow
def test_vscale_logon_selectors():
    print(f'login_url={vscale.login_url}')
    self = vscale.browserengine('test', 'test', 'test', login_url=vscale.login_url, user_selectors=vscale.user_selectors)
    self.main('check_logon')
