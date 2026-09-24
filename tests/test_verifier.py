"""
Unit tests for ResearchVerifier.
Tests rule-based contradiction detection, MCP registry resolution, and platform review classification.
"""

import unittest
from agent.verifier import ResearchVerifier

class TestVerifier(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.verifier = ResearchVerifier()

    def test_enterprise_sales_gate_rule(self):
        """Verify that apps with sales contract blockers are corrected to Blocked P3."""
        fake_app = {
            "id": 999,
            "name": "PitchBook",
            "category": "Finance and Fintech",
            "self_serve_status": "Self-serve Free",
            "buildability_verdict": "Ready (P0 - Immediate Quick Win)",
            "blocker_summary": "No blockers found",
            "api_surface": "REST API",
            "auth_methods": ["API Key"],
            "mcp_status": "None"
        }
        verified = self.verifier.verify_app(fake_app)
        self.assertIn("P3", verified["buildability_verdict"])
        self.assertIn("Partner/Sales Gated", verified["self_serve_status"])
        self.assertTrue(verified["needs_human_review"])

    def test_platform_review_gate_rule(self):
        """Verify that apps requiring developer token or app review are tagged Conditional P2."""
        fake_app = {
            "id": 998,
            "name": "WhatsApp Business",
            "category": "Communications and Messaging",
            "self_serve_status": "Self-serve Trial",
            "buildability_verdict": "Ready (P1 - Standard OAuth)",
            "blocker_summary": "None",
            "api_surface": "Cloud REST API",
            "auth_methods": ["OAuth2"],
            "mcp_status": "None"
        }
        verified = self.verifier.verify_app(fake_app)
        self.assertIn("P2", verified["buildability_verdict"])
        self.assertIn("Meta Business Verification", verified["blocker_summary"])

    def test_mcp_registry_resolution(self):
        """Verify that apps in the official MCP registry are marked as having MCP servers."""
        fake_app = {
            "id": 997,
            "name": "GitHub",
            "category": "Developer, Infra and Data platforms",
            "self_serve_status": "Self-serve Free",
            "buildability_verdict": "Ready (P0 - Immediate Quick Win)",
            "blocker_summary": "None",
            "api_surface": "REST & GraphQL",
            "auth_methods": ["OAuth2", "Personal Access Token"],
            "mcp_status": "None"
        }
        verified = self.verifier.verify_app(fake_app)
        self.assertIn("Official", verified["mcp_status"])

    def test_unofficial_session_cookie_workaround(self):
        """Verify that apps without public APIs relying on session tokens are flagged as P3 Workaround."""
        fake_app = {
            "id": 996,
            "name": "Otter AI",
            "category": "AI, Research and Media-native",
            "self_serve_status": "Self-serve Free",
            "buildability_verdict": "Ready (P0 - Immediate Quick Win)",
            "blocker_summary": "None",
            "api_surface": "REST API",
            "auth_methods": ["API Key"],
            "mcp_status": "None"
        }
        verified = self.verifier.verify_app(fake_app)
        self.assertIn("P3", verified["buildability_verdict"])
        self.assertIn("Unofficial", verified["buildability_verdict"])
        self.assertTrue(verified["needs_human_review"])

if __name__ == "__main__":
    unittest.main()
