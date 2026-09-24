"""
Unit test verifying HTML page integrity and client-side data binding.
"""

import os
import json

def test_html():
    html_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index.html")
    assert os.path.exists(html_path), "index.html does not exist"

    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert len(content) > 100000, "index.html is unexpectedly small"
    assert '"id": 100' in content, "App #100 missing from embedded JSON"
    assert '"id": 1' in content, "App #1 missing from embedded JSON"
    assert "OAuth 2.0" in content, "Patterns missing from HTML"
    assert "hits_and_misses" in content, "Benchmark report missing from HTML"
    assert "switchTab" in content, "Tab switching function missing"
    assert "filterTable" in content, "Filter table function missing"

    print("SUCCESS: index.html passed all integrity and data embedding assertions!")

if __name__ == "__main__":
    test_html()
