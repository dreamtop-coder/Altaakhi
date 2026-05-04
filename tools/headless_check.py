import asyncio
from playwright.sync_api import sync_playwright

URL = 'http://127.0.0.1:8000/invoices/edit/6/'

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, wait_until='networkidle')
        # wait for totals to appear
        try:
            page.wait_for_selector('#services-sub-total', timeout=5000)
            page.wait_for_selector('#sub-total', timeout=5000)
        except Exception:
            pass
        svc = page.eval_on_selector('#services-sub-total', 'el => el.textContent') if page.query_selector('#services-sub-total') else None
        parts = page.eval_on_selector('#sub-total', 'el => el.textContent') if page.query_selector('#sub-total') else None
        grand = page.eval_on_selector('#grand-total', 'el => el.textContent') if page.query_selector('#grand-total') else None
        print('services-sub-total:', svc)
        print('sub-total (parts):', parts)
        print('grand-total:', grand)
        browser.close()

if __name__ == '__main__':
    run()
