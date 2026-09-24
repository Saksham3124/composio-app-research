"""
Main CLI Pipeline for Composio App Research Agent.
Provides commands to execute research, run verification loops, and generate benchmark reports.
"""

import argparse
import sys
import os
import json

from agent.generate_datasets import main as generate_all
from agent.verifier import ResearchVerifier
from agent.benchmark import calculate_benchmark

def run_pipeline():
    parser = argparse.ArgumentParser(description="Composio App Research Agent CLI")
    parser.add_argument(
        "--mode",
        choices=["research", "verify", "benchmark", "all"],
        default="all",
        help="Pipeline phase to execute"
    )
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")

    print("=================================================================")
    print("      COMPOSIO PRODUCT OPS - 100 APPS RESEARCH AGENT PIPELINE    ")
    print("=================================================================\n")

    if args.mode in ["research", "all"]:
        print("[PHASE 1] Executing Automated Research & Extraction Pipeline...")
        generate_all()
        print(" -> Successfully generated data/apps_pass1.json, data/apps_pass2.json, data/apps_final.json\n")

    if args.mode in ["verify", "all"]:
        print("[PHASE 2] Running Verification Loops & Heuristic Contradiction Audits...")
        final_file = os.path.join(data_dir, "apps_final.json")
        verifier = ResearchVerifier(final_file)
        anomalies = verifier.run_rule_audit()
        if not anomalies:
            print(" -> PASS: 0 Contradictions detected across 100 applications in Golden Dataset.")
        else:
            print(f" -> WARNING: {len(anomalies)} anomalies detected.")

        print(" -> Auditing sample URLs for reachability...")
        url_results = verifier.check_urls(sample_size=5)
        for u in url_results:
            status = u.get("status") or u.get("error")
            print(f"    - {u['name']}: {status}")
        print(" -> Verification complete.\n")

    if args.mode in ["benchmark", "all"]:
        print("[PHASE 3] Computing Multi-Pass Accuracy Shift Benchmark...")
        report = calculate_benchmark()
        shift = report["metrics_shift"]
        print(f" -> Pass 1 Baseline Accuracy:    {shift['pass1_raw']['overall_accuracy']}%")
        print(f" -> Pass 2 Verification Loops:   {shift['pass2_loop_verified']['overall_accuracy']}%")
        print(f" -> Pass 3 Human-in-Loop Audit:  {shift['pass3_human_audited']['overall_accuracy']}%\n")

        print("Top Verification Hits & Misses:")
        for hm in report["hits_and_misses"][:3]:
            print(f"  * {hm['app']}:")
            print(f"    Miss: {hm['pass1_miss']}")
            print(f"    Fix:  {hm['verification_loop']}\n")

    print("=================================================================")
    print(" Pipeline execution finished successfully.")
    print(" Open web/index.html to view the interactive executive dashboard.")
    print("=================================================================")

if __name__ == "__main__":
    run_pipeline()
