from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "rw-research-passport" / "scripts" / "passport.py"


class ResearchPassportCliTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(SCRIPT), *args], text=True, capture_output=True, check=False)

    def test_material_registration_and_missing_handoff_material(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            passport = Path(temp_dir) / "passport.json"
            self.assertEqual(0, self.run_cli("init", str(passport), "--project-id", "PROJECT-1", "--title", "Trial project").returncode)
            added = self.run_cli(
                "add-material", str(passport), "--id", "MAT-1", "--type", "paper",
                "--title", "Paper one", "--source-pointer", "doi:10.1000/example", "--status", "verified",
            )
            self.assertEqual(0, added.returncode, added.stdout + added.stderr)
            self.assertEqual(0, self.run_cli("validate", str(passport)).returncode)
            payload = json.loads(passport.read_text(encoding="utf-8"))
            payload["handoffs"].append({
                "id": "HANDOFF-1", "from_stage": "discovery", "to_stage": "extraction",
                "material_ids": ["MAT-MISSING"], "status": "prepared", "recorded_at": payload["updated_at"],
            })
            passport.write_text(json.dumps(payload), encoding="utf-8")
            invalid = self.run_cli("validate", str(passport))
            self.assertEqual(2, invalid.returncode)
            self.assertIn("references missing material", invalid.stdout)


if __name__ == "__main__":
    unittest.main()
