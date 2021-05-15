import pytest
import conftest
import asyncio
from pyppeteer import launch  # pyppeteer - python puppeteer
import importlib.metadata

responses = []
async def response_worker(response):
    print(f'response:{response.request.url},{len(await response.text())}')
    responses.append(f'response:{response.request.url},{len(await response.text())}')

async def main():
    browser = await launch({
    'headless': False,
    'ignoreHTTPSErrors': True,
    'defaultViewport': None,
    'executablePath': 'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
    'args': ["--user-data-dir=c:/temp/clean_profile"]
    })
    pages = await browser.pages()
    for pg in pages[1:]:
        await pg.close() # Close other opened pages
    page = pages[0]  # await browser.newPage()
    page.on("response", response_worker)
    await page.goto('https://example.com')
    txt = await page.content()
    url = page.url
    print(url, len(txt))
    #await page.screenshot({'path': 'example.png'})
    await asyncio.sleep(1)
    await browser.close()

def test_pyppeteer_engine():
    print(f"{importlib.metadata.version('pyee')=}")
    print(f"{importlib.metadata.version('pyppeteer')=}")
    asyncio.get_event_loop().run_until_complete(main())
    assert len(responses) != 0, 'Check make call response_worker == []'
