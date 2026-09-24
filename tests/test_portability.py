r"""
Unit tests for Codebase Portability and Integrity.
Verifies that no machine-specific Windows paths exist in any source code,
datasets, or configuration files across the repository.
"""

import unittest
from pathlib import Path
import os
import re

class TestPortability(unittest.TestCase):
    def setUp(self):
        self.root_dir = Path(__file__).resolve().parent.parent
        self.excluded_dirs = {".git", "venv", ".idea", ".vscode", "__pycache__"}

    def test_no_hardcoded_user_paths(self):
        r"""Scans all tracked files for user machine paths (C:\Users\ or C:/Users/)."""
        offending_files = []
        user_path_pattern = re.compile(r"C:[\\/]Users[\\/][a-zA-Z0-9_-]+", re.IGNORECASE)

        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in self.excluded_dirs]
            for file in files:
                ext = Path(file).suffix.lower()
                if ext in [".py", ".json", ".md", ".yaml", ".yml", ".toml", ".sh"]:
                    file_path = Path(root) / file
                    try:
                        content = file_path.read_text(encoding="utf-8")
                        if user_path_pattern.search(content):
                            # Skip test_portability itself where pattern is defined
                            if file == "test_portability.py":
                                continue
                            offending_files.append(str(file_path.relative_to(self.root_dir)))
                    except Exception:
                        pass

        self.assertEqual(
            offending_files,
            [],
            f"Machine-specific user paths found in files: {offending_files}. Replace with Path(__file__) or relative paths."
        )

    def test_all_expected_datasets_exist(self):
        """Verify that all core pipeline data files exist and are valid JSON."""
        data_dir = self.root_dir / "data"
        expected_files = [
            "apps_seed.json",
            "golden_reference.json",
            "pass1_predictions.json",
            "pass2_verified.json",
            "apps_final.json",
            "mcp_registry.json",
            "human_audit_sample.json",
            "benchmark_report.json",
            "patterns.json"
        ]
        for fname in expected_files:
            target = data_dir / fname
            self.assertTrue(target.exists(), f"Missing required dataset: {fname}")
            try:
                import json
                with open(target, "r", encoding="utf-8") as f:
                    json.load(f)
            except Exception as e:
                self.fail(f"Invalid JSON in {fname}: {e}")

if __name__ == "__main__":
    unittest.main()
