import pytest
import conftest  # type: ignore # ignore import error
import a1by  # pylint: disable=import-error

@pytest.mark.slow
def test_a1by_logon_selectors():
    print(f'login_url={a1by.login_url}')
    self = a1by.browserengine('test', 'test', 'test', login_url=a1by.login_url, user_selectors=a1by.user_selectors)
    self.main('check_logon')
