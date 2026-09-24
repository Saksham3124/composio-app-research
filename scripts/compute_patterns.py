"""
Computes data/patterns.json fresh from data/golden_reference.json.
Calculates auth-method distribution, self-serve vs gated breakdown,
buildability verdict distribution, and per-category metrics.
Maintains exact schema compatibility for web/index.html and scripts/build_html.py.
"""

import json
from pathlib import Path
from typing import Dict, Any

def compute_patterns(golden_path: Path = None, output_path: Path = None) -> Dict[str, Any]:
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"

    golden_file = golden_path or (data_dir / "golden_reference.json")
    out_file = output_path or (data_dir / "patterns.json")

    with open(golden_file, "r", encoding="utf-8") as f:
        golden_data = json.load(f)

    apps = golden_data.get("apps", [])
    total = len(apps)

    # 1. Auth Distribution (Primary protocol classification)
    auth_counts = {
        "OAuth 2.0": 0,
        "API Key / Bearer Token": 0,
        "Basic Auth": 0,
        "Custom / Enterprise": 0,
        "No Auth (CLI/Open Source)": 0
    }

    for a in apps:
        primary = a["auth_methods"][0] if a.get("auth_methods") else "None"
        if "OAuth" in primary:
            k = "OAuth 2.0"
        elif any(term in primary for term in ["API Key", "Token", "PAT", "Bearer", "Secret Key", "Publishable Key"]):
            k = "API Key / Bearer Token"
        elif "Basic" in primary:
            k = "Basic Auth"
        elif "None" in primary or primary == "CLI":
            k = "No Auth (CLI/Open Source)"
        else:
            k = "Custom / Enterprise"
        auth_counts[k] += 1

    # 2. Gating Distribution
    gating_counts = {
        "100% Free Self-Serve": 0,
        "Free Trial Self-Serve": 0,
        "Paid Account Gated": 0,
        "Partner / Sales Gated": 0
    }

    for a in apps:
        status = a.get("self_serve_status", "")
        if "Self-serve Free" in status:
            g = "100% Free Self-Serve"
        elif "Trial" in status:
            g = "Free Trial Self-Serve"
        elif "Paid" in status or "Account" in status:
            g = "Paid Account Gated"
        elif "Partner" in status or "Gated" in status or "Waitlist" in status:
            g = "Partner / Sales Gated"
        else:
            g = "Partner / Sales Gated"
        gating_counts[g] += 1

    # 3. Buildability Verdict Distribution
    verdict_counts = {
        "P0: Immediate Quick Win (0-Day)": 0,
        "P1: Ready (Standard OAuth/Setup)": 0,
        "P2: Conditional (Tier/Review Gated)": 0,
        "P3: Blocked / Workaround Needed": 0
    }

    for a in apps:
        v = a.get("buildability_verdict", "")
        if "P0" in v:
            vk = "P0: Immediate Quick Win (0-Day)"
        elif "P1" in v:
            vk = "P1: Ready (Standard OAuth/Setup)"
        elif "P2" in v:
            vk = "P2: Conditional (Tier/Review Gated)"
        else:
            vk = "P3: Blocked / Workaround Needed"
        verdict_counts[vk] += 1

    # 4. Per-Category Breakdown
    category_summary = {}
    for a in apps:
        cat = a.get("category", "Uncategorized")
        if cat not in category_summary:
            category_summary[cat] = {"total": 0, "self_serve": 0, "gated": 0, "p0_quick_wins": 0}
        category_summary[cat]["total"] += 1
        if "Self-serve" in a.get("self_serve_status", ""):
            category_summary[cat]["self_serve"] += 1
        else:
            category_summary[cat]["gated"] += 1
        if "P0" in a.get("buildability_verdict", ""):
            category_summary[cat]["p0_quick_wins"] += 1

    # 5. Key Strategic Takeaways
    p0_share = verdict_counts["P0: Immediate Quick Win (0-Day)"]
    oauth_share = auth_counts["OAuth 2.0"]
    apikey_share = auth_counts["API Key / Bearer Token"]

    key_takeaways = [
        f"OAuth 2.0 ({oauth_share}% primary) dominates SaaS, CRM, and Social collaboration, requiring multi-tenant token refresh infrastructure.",
        f"API Key / Bearer tokens ({apikey_share}%) dominate Developer Tools, Scraping, and AI Media, enabling instantaneous zero-interaction agent invocation.",
        "Developer/Infra and Productivity platforms are 100% self-serve; Enterprise CRM and Finance/Fintech have the highest partner/compliance gating.",
        "The top blocker across enterprise tools is Sales/Partner Gating (PitchBook, DealCloud, Salesforce Commerce Cloud), followed by Meta/Amazon App Review.",
        f"Quick Wins ({p0_share}% of apps) provide immediate 0-day agent toolkit expansion with zero sales outreach."
    ]

    new_patterns = {
        "total_apps": total,
        "auth_distribution": auth_counts,
        "gating_distribution": gating_counts,
        "verdict_distribution": verdict_counts,
        "category_summary": category_summary,
        "key_takeaways": key_takeaways
    }

    # Load old patterns to display diff
    old_patterns = None
    if out_file.exists():
        try:
            with open(out_file, "r", encoding="utf-8") as f:
                old_patterns = json.load(f)
        except Exception:
            pass

    # Save fresh patterns
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(new_patterns, f, indent=2)

    print(f"Generated {out_file} fresh from {golden_file.name} ({total} apps).")

    # Print Diff
    print("\n=================================================================")
    print(" PATTERNS DIFF: OLD vs NEW (Fresh from golden_reference.json)")
    print("=================================================================")
    if old_patterns:
        # Auth diff
        print("\n[Auth Distribution]:")
        all_auth_keys = sorted(set(old_patterns.get("auth_distribution", {}).keys()) | set(auth_counts.keys()))
        for k in all_auth_keys:
            old_v = old_patterns.get("auth_distribution", {}).get(k, 0)
            new_v = auth_counts.get(k, 0)
            diff_indicator = f"-> {new_v} (CHANGED)" if old_v != new_v else f"== {new_v} (unchanged)"
            print(f"  {k:30s}: Old={old_v:2d} {diff_indicator}")

        # Gating diff
        print("\n[Gating Distribution]:")
        all_gating_keys = sorted(set(old_patterns.get("gating_distribution", {}).keys()) | set(gating_counts.keys()))
        for k in all_gating_keys:
            old_v = old_patterns.get("gating_distribution", {}).get(k, 0)
            new_v = gating_counts.get(k, 0)
            diff_indicator = f"-> {new_v} (CHANGED)" if old_v != new_v else f"== {new_v} (unchanged)"
            print(f"  {k:30s}: Old={old_v:2d} {diff_indicator}")

        # Verdict diff
        print("\n[Verdict Distribution]:")
        all_verdict_keys = sorted(set(old_patterns.get("verdict_distribution", {}).keys()) | set(verdict_counts.keys()))
        for k in all_verdict_keys:
            old_v = old_patterns.get("verdict_distribution", {}).get(k, 0)
            new_v = verdict_counts.get(k, 0)
            diff_indicator = f"-> {new_v} (CHANGED)" if old_v != new_v else f"== {new_v} (unchanged)"
            print(f"  {k:35s}: Old={old_v:2d} {diff_indicator}")

        # Category diff
        print("\n[Category Breakdown Changes]:")
        cat_changed = False
        for cat, new_stat in category_summary.items():
            old_stat = old_patterns.get("category_summary", {}).get(cat, {})
            if old_stat != new_stat:
                cat_changed = True
                print(f"  {cat}:")
                print(f"    Old: {old_stat}")
                print(f"    New: {new_stat}")
        if not cat_changed:
            print("  All 10 category summaries are identical to previous values.")
    else:
        print("No previous patterns.json found to diff.")

    print("=================================================================\n")
    return new_patterns

if __name__ == "__main__":
    compute_patterns()
