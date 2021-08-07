import pytest
import conftest  # type: ignore # ignore import error
import beeline_uz  # pylint: disable=import-error

@pytest.mark.slow
def test_beeline_uz_logon_selectors():
    print(f'login_url{beeline_uz.login_url}')
    self = beeline_uz.browserengine('test', 'test', 'test', login_url=beeline_uz.login_url, user_selectors=beeline_uz.user_selectors)
    self.main('check_logon')
