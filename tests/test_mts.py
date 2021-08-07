import pytest
import importlib.metadata
import conftest  # type: ignore # ignore import error
import mts  # pylint: disable=import-error

# Открываем основную страницу чтобы в response попали страницы для проверки что response отрабатывает
class balance_over_mts(mts.browserengine):
    def check_logon_selectors_prepare(self):
        self.page_goto('https://mts.ru')

@pytest.mark.slow
def test_mts2_logon_selectors():
    # pytest.set_trace() # breakpoint 
    # assert 0 # uncomment for post mortem debug and run py.test --pdb
    print(f'login_url={mts.login_url}')
    print(f"{importlib.metadata.version('pyee')=}")
    print(f"{importlib.metadata.version('pyppeteer')=}")
    self = balance_over_mts('test', 'test', 'test', login_url=mts.login_url, user_selectors=mts.user_selectors)
    self.main('check_logon')
    assert len(self.responses) != 0, 'Check make call response_worker == []'

