'Проверка установки с нуля по сложному пути'
import re, os, tempfile
import pytest
import requests
import conftest  # type: ignore # ignore import error

import compile_all_jsmblh  # pylint: disable=import-error
import dbengine  # pylint: disable=import-error
import dll_call_test  # pylint: disable=import-error
import get_icon  # pylint: disable=import-error
import httpserver_mobile  # pylint: disable=import-error
import make_stock_stat  # pylint: disable=import-error
import browsercontroller  # pylint: disable=import-error
import settings  # pylint: disable=import-error
import store  # pylint: disable=import-error


def test_module_import():
    pass