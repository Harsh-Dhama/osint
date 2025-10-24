import asyncio
import pytest
from backend.modules.whatsapp_scraper import WhatsAppScraper

@pytest.mark.asyncio
async def test_qr_debug_artifacts_when_not_found(monkeypatch, tmp_path):
    s = WhatsAppScraper(session_file=str(tmp_path / "state.json"))

    class DummyPage:
        async def goto(self, *a, **k):
            pass
        async def wait_for_selector(self, *a, **k):
            raise Exception("not found")
        async def query_selector(self, *a, **k):
            return None
        async def screenshot(self, *a, **k):
            return b""
        async def content(self):
            return "<html></html>"

    s.page = DummyPage()
    res = await s.get_qr_code()
    assert res is None
    # debug paths may be set
    assert s.last_debug_html is None or s.last_debug_html.endswith('.html')

@pytest.mark.asyncio
async def test_rate_limit_spacing():
    s = WhatsAppScraper()
    s.last_request_time = 0
    start = asyncio.get_event_loop().time()
    await s._rate_limit_check()
    end = asyncio.get_event_loop().time()
    # first call should not wait 12s, since last_request_time is 0
    assert end - start < 1.0
