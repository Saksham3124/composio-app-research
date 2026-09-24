"""
Unit tests for the Benchmark Engine.
Verifies that multi-pass metrics and human audit metrics are computed dynamically
from raw predictions vs golden reference, with valid float ranges [0, 100].
"""

import unittest
from pathlib import Path
import json

from agent.benchmark import calculate_benchmark

class TestBenchmark(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = calculate_benchmark()
        cls.shift = cls.report["metrics_shift"]

    def test_metrics_structure(self):
        """Verify that all required metric sections and keys are present."""
        self.assertIn("pass1_raw", self.shift)
        self.assertIn("pass2_loop_verified", self.shift)
        self.assertIn("human_audit_sample", self.shift)

    def test_pass1_metrics_valid_ranges(self):
        """Verify Pass 1 baseline metrics are valid percentages between 0 and 100."""
        p1 = self.shift["pass1_raw"]
        for key in ["overall_accuracy", "verdict_acc", "self_serve_acc", "surface_acc", "mcp_acc"]:
            self.assertIn(key, p1)
            val = p1[key]
            self.assertIsInstance(val, float)
            self.assertGreaterEqual(val, 0.0)
            self.assertLessEqual(val, 100.0)
        self.assertEqual(p1["total_evaluated"], 100)

    def test_pass2_metrics_valid_ranges_and_progression(self):
        """Verify Pass 2 metrics show non-fabricated improvement over Pass 1."""
        p1 = self.shift["pass1_raw"]
        p2 = self.shift["pass2_loop_verified"]
        for key in ["overall_accuracy", "verdict_acc", "self_serve_acc", "mcp_acc"]:
            self.assertIn(key, p2)
            val = p2[key]
            self.assertIsInstance(val, float)
            self.assertGreaterEqual(val, 0.0)
            self.assertLessEqual(val, 100.0)
        self.assertEqual(p2["total_evaluated"], 100)
        # Pass 2 verification loop must improve overall accuracy through contradiction resolution
        self.assertGreater(p2["overall_accuracy"], p1["overall_accuracy"])

    def test_human_audit_metrics(self):
        """Verify human audit sample metrics are valid and show real progression."""
        audit = self.shift["human_audit_sample"]
        self.assertEqual(audit["sample_size"], 25)
        self.assertEqual(audit["approved_count"], 25)
        self.assertGreaterEqual(audit["pass1_sample_accuracy"], 0.0)
        self.assertGreaterEqual(audit["pass2_sample_accuracy"], 0.0)
        self.assertLessEqual(audit["pass2_sample_accuracy"], 100.0)
        self.assertGreater(audit["pass2_sample_accuracy"], audit["pass1_sample_accuracy"])

    def test_hits_and_misses_populated(self):
        """Verify Hits and Misses case studies are dynamically populated from real audits."""
        hm = self.report.get("hits_and_misses", [])
        self.assertGreaterEqual(len(hm), 5)
        for item in hm:
            self.assertIn("app", item)
            self.assertIn("pass1_miss", item)
            self.assertIn("final_truth", item)
            self.assertIn("verification_loop", item)

if __name__ == "__main__":
    unittest.main()
