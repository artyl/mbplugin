import re
import pytest
import requests
import conftest
import strelka  # pylint: disable=import-error

def test_strelka():
    assert strelka.get_card_info('12345678901') == {"__all__":["Карта не найдена"]}
