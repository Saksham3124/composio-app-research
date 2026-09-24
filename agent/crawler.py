"""
Web crawler and documentation fetcher for the Composio Research Agent.
Supports fetching developer documentation, inspecting HTTP status codes,
and scanning for authentication keywords, pricing gates, and MCP references.
"""

import requests
import json
import re
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional

HEADERS = {
    "User-Agent": "Composio-Research-Agent/1.0 (+https://composio.dev; ProductOps-Intern-Evaluation)"
}

class DocCrawler:
    def __init__(self, timeout: int = 10):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.timeout = timeout

    def check_url(self, url: str) -> Dict[str, Any]:
        """Validate URL reachability and extract basic metadata."""
        if not url.startswith("http"):
            url = "https://" + url
        try:
            resp = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            soup = BeautifulSoup(resp.text, "html.parser")
            title = soup.title.string.strip() if soup.title and soup.title.string else ""
            
            # Simple keyword checks for verification
            text_sample = resp.text[:10000].lower()
            has_oauth = "oauth" in text_sample
            has_apikey = "api key" in text_sample or "api-key" in text_sample or "token" in text_sample
            has_graphql = "graphql" in text_sample
            has_mcp = "mcp" in text_sample or "model context protocol" in text_sample

            return {
                "valid": resp.status_code in [200, 201, 301, 302],
                "status_code": resp.status_code,
                "final_url": str(resp.url),
                "title": title,
                "signals": {
                    "has_oauth": has_oauth,
                    "has_apikey": has_apikey,
                    "has_graphql": has_graphql,
                    "has_mcp": has_mcp
                }
            }
        except Exception as e:
            return {
                "valid": False,
                "status_code": None,
                "error": str(e),
                "signals": {}
            }

if __name__ == "__main__":
    crawler = DocCrawler()
    test = crawler.check_url("https://developers.hubspot.com/docs/api/overview")
    print(json.dumps(test, indent=2))
