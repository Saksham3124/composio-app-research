"""
Documentation retrieval and signal extraction module for the Composio Research Agent.
Uses requests, BeautifulSoup, and heuristic pattern detection to identify authentication,
API architecture, pricing gates, and MCP ecosystem signals from live developer docs.
"""

import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional

try:
    from agent.models import CrawlResult, CrawlSignal
except ImportError:
    from models import CrawlResult, CrawlSignal

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 ComposioResearchAgent/1.1"
}

class DocCrawler:
    def __init__(self, timeout: int = 8):
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self.timeout = timeout

    def check_url(self, url: str) -> CrawlResult:
        """Validate URL reachability and extract structured developer documentation signals."""
        if not url.startswith("http"):
            url = "https://" + url

        try:
            resp = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            text_sample = resp.text[:15000].lower()
            soup = BeautifulSoup(resp.text[:30000], "html.parser")
            title = soup.title.string.strip() if (soup.title and soup.title.string) else ""

            # Signal extraction
            signals = CrawlSignal(
                has_oauth=bool(re.search(r"\boauth\b|\bauthorization code\b|\bpkce\b", text_sample)),
                has_apikey=bool(re.search(r"\bapi[ _-]key\b|\bprivate key\b|\bsecret key\b", text_sample)),
                has_basic_auth=bool(re.search(r"\bbasic auth\b|\busername and password\b", text_sample)),
                has_bearer=bool(re.search(r"\bbearer token\b|\bpersonal access token\b|\bjwt\b", text_sample)),
                has_graphql=bool(re.search(r"\bgraphql\b|\bmutations\b|\bqueries\b", text_sample)),
                has_rest=bool(re.search(r"\brest api\b|\bendpoint\b|\bpost\b|\bget\b", text_sample)),
                has_cli=bool(re.search(r"\bcli\b|\bcommand[ _-]line\b|\bnpm install\b|\bpip install\b", text_sample)),
                has_mcp=bool(re.search(r"\bmcp\b|\bmodel context protocol\b|\bsmithery\b", text_sample)),
                has_free_tier=bool(re.search(r"\bfree tier\b|\bfree plan\b|\bforever free\b|\bdeveloper tier\b", text_sample)),
                has_trial=bool(re.search(r"\bfree trial\b|\b14-day\b|\b30-day\b|\btrial\b", text_sample)),
                has_sales_gate=bool(re.search(r"\bcontact sales\b|\brequest demo\b|\bschedule a call\b|\benterprise only\b", text_sample)),
                has_pricing_wall=bool(re.search(r"\bpaid subscription\b|\bbilling required\b|\bcredit card\b", text_sample))
            )

            return CrawlResult(
                valid=resp.status_code in [200, 201, 301, 302],
                status_code=resp.status_code,
                final_url=str(resp.url),
                title=title,
                signals=signals,
                error=None
            )
        except Exception as e:
            return CrawlResult(
                valid=False,
                status_code=None,
                final_url=url,
                title="",
                signals=CrawlSignal(),
                error=str(e)
            )

if __name__ == "__main__":
    crawler = DocCrawler()
    res = crawler.check_url("https://developers.hubspot.com/docs/api/overview")
    print("Status:", res.status_code)
    print("Title:", res.title)
    print("Signals:", res.signals.model_dump())
