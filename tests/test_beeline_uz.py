import pytest
import conftest
import beeline_uz  # pylint: disable=import-error

# Игнорирование RuntimeWarning пришлось включить из-за того что pytest думает что нужен await в 
# self.browser.on("disconnected", self.disconnected_worker)
# и ругается - RuntimeWarning: coroutine ..... was never awaited
@pytest.mark.filterwarnings('ignore::RuntimeWarning')
@pytest.mark.slow
def test_beeline_uz_logon_selectors():
    print(f'login_url{beeline_uz.login_url}')
    self = beeline_uz.browserengine('test', 'test', 'test', login_url=beeline_uz.login_url, user_selectors=beeline_uz.user_selectors)
    self.main('check_logon')
