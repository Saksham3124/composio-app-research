"""
Automated Research Pipeline for Composio App Feasibility Analysis.
Ingests app seeds, crawls documentation, extracts signals, applies structured classification rules,
and outputs Pass 1 predictions.
Uses pathlib for cross-platform portability.
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, Any, List

try:
    from agent.crawler import DocCrawler
    from agent.models import AppSeed, AppRecord
except ImportError:
    from crawler import DocCrawler
    from models import AppSeed, AppRecord

BASE_DIR = Path(__file__).resolve().parent.parent

class ResearchPipeline:
    def __init__(self, seed_file: Path = None):
        self.seed_file = seed_file or (BASE_DIR / "data" / "apps_seed.json")
        self.crawler = DocCrawler(timeout=6)
        with open(self.seed_file, "r", encoding="utf-8") as f:
            self.seeds = json.load(f)["apps"]

    def resolve_docs_url(self, seed: Dict[str, Any]) -> str:
        """Determines best target documentation URL from seed hint."""
        hint = seed.get("hint", "").strip()
        name = seed["name"]
        
        # Extract url from hint if present
        url_match = re.search(r"([a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s()]*)?)", hint)
        if url_match:
            candidate = url_match.group(1).rstrip(")")
            if not candidate.startswith("http"):
                return f"https://{candidate}"
            return candidate

        # Standard heuristics
        clean_name = re.sub(r"[^a-zA-Z0-9]", "", name).lower()
        return f"https://docs.{clean_name}.com"

    def classify_app(self, seed: Dict[str, Any], crawl_res: Any) -> Dict[str, Any]:
        """
        Classifies an application based on extracted signals, seed hints, and architectural rules.
        Produces Pass 1 automated predictions.
        """
        name = seed["name"]
        category = seed["category"]
        hint = seed.get("hint", "")
        signals = crawl_res.signals

        # 1. Determine Auth Methods
        auth_methods = []
        if signals.has_oauth or "oauth" in hint.lower():
            auth_methods.append("OAuth2")
        if signals.has_apikey or signals.has_bearer or "api key" in hint.lower():
            auth_methods.append("API Key")
        if signals.has_basic_auth:
            auth_methods.append("Basic Auth")
        if signals.has_cli or "cli" in hint.lower():
            auth_methods.append("None (Open Source CLI)" if not auth_methods else "CLI Token")

        if not auth_methods:
            # Fallback to category default heuristic
            if category in ["CRM and Sales", "Support and Helpdesk", "Communications and Messaging"]:
                auth_methods = ["OAuth2"]
            else:
                auth_methods = ["API Key"]

        # 2. Determine API Surface
        if signals.has_graphql and signals.has_rest:
            api_surface = "REST and GraphQL"
            breadth = "Very Broad (>200 endpoints)"
        elif signals.has_graphql:
            api_surface = "GraphQL API"
            breadth = "Broad (>80 operations)"
        elif signals.has_cli or "cli" in hint.lower():
            api_surface = "CLI / Local Executable"
            breadth = "CLI Utility"
        elif crawl_res.valid:
            api_surface = "REST API"
            breadth = "Broad (>100 endpoints)"
        else:
            api_surface = "Web API / Undocumented"
            breadth = "Narrow / Unknown"

        # 3. Determine Self-Serve Status
        if signals.has_sales_gate and not signals.has_free_tier:
            self_serve_status = "Partner/Sales Gated"
            self_serve_details = "Sales contact required for enterprise licensing."
        elif signals.has_trial and not signals.has_free_tier:
            self_serve_status = "Self-serve Trial"
            self_serve_details = "Free trial available upon signup."
        elif signals.has_pricing_wall and not signals.has_free_tier:
            self_serve_status = "Paid Plan Gated"
            self_serve_details = "API access requires paid tier subscription."
        else:
            self_serve_status = "Self-serve Free"
            self_serve_details = "Developer registration or free tier available."

        # 4. Determine MCP Status
        if signals.has_mcp or "mcp" in hint.lower():
            mcp_status = "Official / Community MCP"
        else:
            mcp_status = "None"

        # 5. Determine Buildability Verdict & Blocker
        if self_serve_status == "Partner/Sales Gated":
            verdict = "Blocked (P3 - Partner/Sales Gate)"
            blocker = "Requires enterprise sales agreement and custom contract provisioning."
        elif self_serve_status == "Paid Plan Gated":
            verdict = "Conditional (P2 - Tier/Review Gated)"
            blocker = "Requires active paid subscription to unlock developer credentials."
        elif "OAuth2" in auth_methods and category in ["Marketing, Ads, Email and Social"]:
            verdict = "Conditional (P2 - Tier/Review Gated)"
            blocker = "Platform app review or developer token approval required for production access."
        elif "OAuth2" in auth_methods and len(auth_methods) == 1:
            verdict = "Ready (P1 - Standard OAuth)"
            blocker = "Requires OAuth 2.0 app configuration and redirect URI management."
        else:
            verdict = "Ready (P0 - Immediate Quick Win)"
            blocker = "None for standard developer access."

        return {
            "id": seed["id"],
            "name": name,
            "category": category,
            "one_liner": f"{category} software tool ({name})",
            "website": f"https://{seed['hint'].split()[0]}" if not seed['hint'].startswith("http") else seed['hint'].split()[0],
            "docs_url": crawl_res.final_url or self.resolve_docs_url(seed),
            "auth_methods": auth_methods,
            "auth_details": f"Authentication managed via {', '.join(auth_methods)}.",
            "self_serve_status": self_serve_status,
            "self_serve_details": self_serve_details,
            "api_surface": api_surface,
            "api_breadth": breadth,
            "mcp_status": mcp_status,
            "buildability_verdict": verdict,
            "blocker_summary": blocker,
            "composio_fit": f"Automated agent integration for {name} workflows.",
            "evidence_url": crawl_res.final_url or self.resolve_docs_url(seed),
            "confidence": 0.85 if crawl_res.valid else 0.60,
            "needs_human_review": not crawl_res.valid or ("Blocked" in verdict)
        }

    def run_pass1(self, sample_limit: int = None, max_workers: int = 12) -> List[Dict[str, Any]]:
        """Executes Pass 1 automated research across all apps concurrently."""
        from concurrent.futures import ThreadPoolExecutor, as_completed

        target_seeds = self.seeds[:sample_limit] if sample_limit else self.seeds
        results_by_id = {}

        print(f"Executing Pass 1 research pipeline across {len(target_seeds)} applications ({max_workers} workers)...")

        def process_seed(seed):
            url = self.resolve_docs_url(seed)
            crawl_res = self.crawler.check_url(url)
            return self.classify_app(seed, crawl_res)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_seed = {executor.submit(process_seed, s): s for s in target_seeds}
            for future in as_completed(future_to_seed):
                try:
                    res = future.result()
                    results_by_id[res["id"]] = res
                except Exception as e:
                    s = future_to_seed[future]
                    print(f"Error processing {s['name']}: {e}")

        # Preserve seed ordering
        results = [results_by_id[s["id"]] for s in target_seeds if s["id"] in results_by_id]

        out_path = BASE_DIR / "data" / "pass1_predictions.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({"apps": results}, f, indent=2)

        print(f"Pass 1 complete. Saved {len(results)} predictions to {out_path}.")
        return results

def run_pass1(sample_limit: int = None, max_workers: int = 12) -> List[Dict[str, Any]]:
    """Convenience function to run Pass 1 pipeline."""
    pipeline = ResearchPipeline()
    return pipeline.run_pass1(sample_limit=sample_limit, max_workers=max_workers)

if __name__ == "__main__":
    run_pass1()
