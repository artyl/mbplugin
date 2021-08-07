import pytest
import conftest  # type: ignore # ignore import error
import megafonb2b  # pylint: disable=import-error

@pytest.mark.slow
def test_megafonb2b_logon_selectors():
    print(f'login_url={megafonb2b.login_url}')
    self = megafonb2b.browserengine('test', 'test', 'test', login_url=megafonb2b.login_url, user_selectors=megafonb2b.user_selectors)
    self.main('check_logon')
