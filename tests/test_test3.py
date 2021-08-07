import pytest
import conftest  # type: ignore # ignore import error
import test3  # pylint: disable=import-error

@pytest.mark.slow
def test_test3_logon_selectors():
    print(f'login_url={test3.login_url}')
    self = test3.browserengine('test', 'test', 'test', login_url=test3.login_url, user_selectors=test3.user_selectors)
    self.main('check_logon')
