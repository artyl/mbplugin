import pytest
import conftest  # type: ignore # ignore import error
import rostelecom  # pylint: disable=import-error

@pytest.mark.slow
def test_rostelecom_logon_selectors():
    print(f'login_url={rostelecom.login_url}')
    self = rostelecom.browserengine('test', 'test', 'test', login_url=rostelecom.login_url, user_selectors=rostelecom.user_selectors, headless=False)
    self.main('check_logon')
