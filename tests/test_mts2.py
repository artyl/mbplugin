import pytest
import importlib.metadata
import conftest
import mts2  # pylint: disable=import-error

# Открываем основную страницу чтобы в response попали страницы для проверки что response отрабатывает
class balance_over_mts2(mts2.browserengine):
    def check_logon_selectors_prepare(self):
        self.page_goto('https://mts.ru')

# Игнорирование RuntimeWarning пришлось включить из-за того что pytest думает что нужен await в 
# self.browser.on("disconnected", self.disconnected_worker)
# и ругается - RuntimeWarning: coroutine ..... was never awaited
@pytest.mark.filterwarnings('ignore::RuntimeWarning')
@pytest.mark.slow
def test_mts2_logon_selectors():
    # pytest.set_trace() # breakpoint 
    # assert 0 # uncomment for post mortem debug and run py.test --pdb
    print(f'login_url={mts2.login_url}')
    print(f"{importlib.metadata.version('pyee')=}")
    print(f"{importlib.metadata.version('pyppeteer')=}")
    self = balance_over_mts2('test', 'test', 'test', login_url=mts2.login_url, user_selectors=mts2.user_selectors)
    self.main('check_logon')
    assert len(self.responses) != 0, 'Check make call response_worker == []'

