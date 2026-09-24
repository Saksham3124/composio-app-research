"""
Syncs data/human_audit_sample.json with the real pipeline outputs from
data/pass1_predictions.json and data/pass2_verified.json.

Overwrites pass1_agent_verdict and pass2_agent_verdict with the real buildability_verdict,
recomputes pass1_verdict_match and pass2_verdict_match against ground_truth_verdict,
and leaves all human audit metadata (evidence URL, rationale, review decision) intact.
"""

import json
from pathlib import Path

def sync_audit_sample():
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"

    pass1_file = data_dir / "pass1_predictions.json"
    pass2_file = data_dir / "pass2_verified.json"
    audit_file = data_dir / "human_audit_sample.json"

    with open(pass1_file, "r", encoding="utf-8") as f:
        pass1_apps = {a["id"]: a for a in json.load(f)["apps"]}

    with open(pass2_file, "r", encoding="utf-8") as f:
        pass2_apps = {a["id"]: a for a in json.load(f)["apps"]}

    with open(audit_file, "r", encoding="utf-8") as f:
        audit_data = json.load(f)

    records = audit_data["records"]
    changed_records_count = 0
    diffs = []

    print(f"Loaded {len(records)} audit records from {audit_file.name}.")
    print("Synchronizing with real pass1 and pass2 predictions...\n")

    for rec in records:
        app_id = rec["app_id"]
        name = rec["name"]
        ground_truth = rec["ground_truth_verdict"]

        if app_id not in pass1_apps:
            raise KeyError(f"App ID {app_id} ({name}) not found in {pass1_file.name}")
        if app_id not in pass2_apps:
            raise KeyError(f"App ID {app_id} ({name}) not found in {pass2_file.name}")

        old_p1_verdict = rec.get("pass1_agent_verdict")
        old_p2_verdict = rec.get("pass2_agent_verdict")
        old_p1_match = rec.get("pass1_verdict_match")
        old_p2_match = rec.get("pass2_verdict_match")

        # Extract REAL verdicts
        real_p1_verdict = pass1_apps[app_id]["buildability_verdict"]
        real_p2_verdict = pass2_apps[app_id]["buildability_verdict"]

        # Recompute exact boolean matches against ground_truth_verdict
        new_p1_match = (real_p1_verdict == ground_truth)
        new_p2_match = (real_p2_verdict == ground_truth)

        # Detect changes
        has_changed = (
            old_p1_verdict != real_p1_verdict or
            old_p2_verdict != real_p2_verdict or
            old_p1_match != new_p1_match or
            old_p2_match != new_p2_match
        )

        if has_changed:
            changed_records_count += 1
            diff_entry = {
                "app_id": app_id,
                "name": name,
                "ground_truth": ground_truth,
                "pass1": {
                    "old_verdict": old_p1_verdict,
                    "new_verdict": real_p1_verdict,
                    "old_match": old_p1_match,
                    "new_match": new_p1_match
                },
                "pass2": {
                    "old_verdict": old_p2_verdict,
                    "new_verdict": real_p2_verdict,
                    "old_match": old_p2_match,
                    "new_match": new_p2_match
                }
            }
            diffs.append(diff_entry)

        # Apply updates
        rec["pass1_agent_verdict"] = real_p1_verdict
        rec["pass2_agent_verdict"] = real_p2_verdict
        rec["pass1_verdict_match"] = new_p1_match
        rec["pass2_verdict_match"] = new_p2_match

    # Write corrected data back to file
    with open(audit_file, "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2)

    print("=================================================================")
    print(f" SYNC COMPLETE: {changed_records_count} of {len(records)} records updated")
    print("=================================================================\n")

    for d in diffs:
        print(f"App #{d['app_id']} - {d['name']}:")
        print(f"  Ground Truth: {d['ground_truth']}")
        if d['pass1']['old_verdict'] != d['pass1']['new_verdict'] or d['pass1']['old_match'] != d['pass1']['new_match']:
            print(f"  Pass 1 Verdict: '{d['pass1']['old_verdict']}' -> '{d['pass1']['new_verdict']}'")
            print(f"  Pass 1 Match:   {d['pass1']['old_match']} -> {d['pass1']['new_match']}")
        else:
            print(f"  Pass 1 Verdict: '{d['pass1']['new_verdict']}' (Match: {d['pass1']['new_match']}) [unchanged]")

        if d['pass2']['old_verdict'] != d['pass2']['new_verdict'] or d['pass2']['old_match'] != d['pass2']['new_match']:
            print(f"  Pass 2 Verdict: '{d['pass2']['old_verdict']}' -> '{d['pass2']['new_verdict']}'")
            print(f"  Pass 2 Match:   {d['pass2']['old_match']} -> {d['pass2']['new_match']}")
        else:
            print(f"  Pass 2 Verdict: '{d['pass2']['new_verdict']}' (Match: {d['pass2']['new_match']}) [unchanged]")
        print()

    # Recomputed summary statistics
    p1_matches_total = sum(1 for r in records if r["pass1_verdict_match"])
    p2_matches_total = sum(1 for r in records if r["pass2_verdict_match"])
    print("-----------------------------------------------------------------")
    print("Summary of Real Verdict Matches on Human Audit Sample (25 apps):")
    print(f"  Real Pass 1 Verdict Matches: {p1_matches_total} / {len(records)} ({p1_matches_total / len(records) * 100:.1f}%)")
    print(f"  Real Pass 2 Verdict Matches: {p2_matches_total} / {len(records)} ({p2_matches_total / len(records) * 100:.1f}%)")
    print("-----------------------------------------------------------------")

if __name__ == "__main__":
    sync_audit_sample()
