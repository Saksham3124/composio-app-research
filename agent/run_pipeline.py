"""
Main CLI Pipeline for Composio App Research Agent.
Provides unified commands to execute live crawl, run verification loops,
compute dynamic benchmarks against golden reference, and build the executive dashboard.
"""

import argparse
import sys
from pathlib import Path

from agent.pipeline import run_pass1
from agent.verifier import run_pass2, ResearchVerifier
from agent.benchmark import calculate_benchmark
from scripts.build_html import generate_html

def run_pipeline():
    parser = argparse.ArgumentParser(description="Composio App Research Agent CLI")
    parser.add_argument(
        "--mode",
        choices=["crawl", "verify", "benchmark", "all"],
        default="all",
        help="Pipeline phase to execute (default: all)"
    )
    parser.add_argument(
        "--skip-crawl",
        action="store_true",
        help="Skip live network crawl and use existing pass1 predictions"
    )
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"

    print("=================================================================")
    print("      COMPOSIO PRODUCT OPS - 100 APPS RESEARCH AGENT PIPELINE    ")
    print("=================================================================\n")

    if args.mode in ["crawl", "all"]:
        print("[PHASE 1] Executing Automated Research & Extraction Pipeline (Pass 1)...")
        if args.skip_crawl:
            print(" -> Skipping live network crawl (--skip-crawl set). Using existing data/pass1_predictions.json.")
        else:
            predictions = run_pass1(max_workers=10)
            print(f" -> Completed Pass 1 extraction for {len(predictions)} applications -> data/pass1_predictions.json\n")

    if args.mode in ["verify", "all"]:
        print("[PHASE 2] Running Verification Loops & Heuristic Contradiction Audits (Pass 2)...")
        verified_apps = run_pass2()
        print(f" -> Automated verification complete for {len(verified_apps)} applications -> data/pass2_verified.json")

        final_file = data_dir / "apps_final.json"
        verifier = ResearchVerifier(str(final_file))
        anomalies = verifier.run_rule_audit()
        if not anomalies:
            print(" -> PASS: 0 Contradictions detected across 100 applications in Golden Dataset.")
        else:
            print(f" -> Flagged {len(anomalies)} items for human review.")

        print(" -> Auditing sample URLs for reachability...")
        url_results = verifier.check_urls(sample_size=5)
        for u in url_results:
            status = u.get("status") or u.get("error")
            print(f"    - {u['name']}: {status}")
        print(" -> Verification complete.\n")

    if args.mode in ["benchmark", "all"]:
        print("[PHASE 3] Computing Dynamic Multi-Pass Accuracy Shift Benchmark...")
        report = calculate_benchmark()
        shift = report["metrics_shift"]
        p1 = shift["pass1_raw"]
        p2 = shift["pass2_loop_verified"]
        audit = shift["human_audit_sample"]

        print(f" -> Pass 1 Baseline Overall Accuracy:  {p1['overall_accuracy']}%")
        print(f"    - Verdict Acc: {p1['verdict_acc']}%, Self-Serve Acc: {p1['self_serve_acc']}%, MCP Acc: {p1['mcp_acc']}%")
        print(f" -> Pass 2 Verified Overall Accuracy:  {p2['overall_accuracy']}%")
        print(f"    - Verdict Acc: {p2['verdict_acc']}%, Self-Serve Acc: {p2['self_serve_acc']}%, MCP Acc: {p2['mcp_acc']}%")
        print(f" -> Human Stratified Audit (25 Apps):   {audit['pass2_sample_accuracy']}% Verdict Match ({audit['approved_count']}/{audit['sample_size']} Approved)\n")

        print("Top Verification Hits & Misses Audited:")
        for hm in report["hits_and_misses"][:3]:
            print(f"  * {hm['app']}:")
            print(f"    Miss: {hm['pass1_miss']}")
            print(f"    Fix:  {hm['verification_loop']}\n")

    if args.mode == "all":
        print("[PHASE 4] Recompiling Executive Standalone Web Dashboard...")
        generate_html()

    print("=================================================================")
    print(" Pipeline execution finished successfully.")
    print(" Open web/index.html or index.html to view the interactive dashboard.")
    print("=================================================================")

if __name__ == "__main__":
    run_pipeline()
