import json
import tempfile
import unittest
from pathlib import Path

from scripts.check_public_privacy import skillhub_source_failures


class SkillHubPrivacyTests(unittest.TestCase):
    def test_privacy_check_uses_skillhub_source_validation(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            skill = Path(temporary_directory) / "rw-test"
            references = skill / "references"
            references.mkdir(parents=True)
            (skill / "SKILL.md").write_text("# Test\n", encoding="utf-8")
            record = {
                "id": "TEST-001",
                "knowledge": "This private_local marker must fail.",
                "source": "packaged_method",
                "source_kind": "packaged_method",
            }
            (references / "atoms.jsonl").write_text(
                json.dumps(record) + "\n",
                encoding="utf-8",
            )

            failures = skillhub_source_failures(skill)

        self.assertEqual(len(failures), 1)
        self.assertIn("private marker remains", failures[0])


if __name__ == "__main__":
    unittest.main()
