#!/usr/bin/env python3
"""Exercise the voice-measurement CLI only in disposable instances."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().with_name("measure_voice.py")
CORPUS = """# Synthetic submitted source

## Verbatim

> This deliberately synthetic narrative contains enough words to exercise the measurement command without using any private author's submitted writing in a public regression fixture.
> A second sufficiently long sentence verifies that the command accepts the instance root and writes its measured output only to the requested temporary destination.

## Draft

> pivotal pivotal pivotal pivotal pivotal pivotal pivotal pivotal
"""
SCAFFOLD = "# Voice\n\nKeep this preamble.\n\n## The fingerprint\n\nOld.\n\n## Provenance\n\nOld.\n"


class VoiceCliTests(unittest.TestCase):
    def test_instance_argument_and_legacy_alias_write_requested_output(self):
        for flag in ("--instance", "--brain"):
            for absolute in (False, True):
                with self.subTest(flag=flag, absolute=absolute), tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    (root / "grants").mkdir()
                    (root / "USER").mkdir()
                    source = root / "grants" / "synthetic.md"
                    source.write_text(CORPUS, encoding="utf-8")
                    protected = root / "USER" / "human.md"
                    protected.write_text("Human-owned; unchanged.\n", encoding="utf-8")
                    output = root / "USER" / "VOICE.md"
                    output.write_text(SCAFFOLD, encoding="utf-8")
                    out_arg = str(output) if absolute else "USER/VOICE.md"
                    result = subprocess.run(
                        [sys.executable, str(SCRIPT), flag, str(root), "--out", out_arg],
                        cwd=root, capture_output=True, text=True, check=False,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    text = output.read_text(encoding="utf-8")
                    self.assertTrue(text.startswith("# Voice\n\nKeep this preamble.\n\n"))
                    self.assertIn("2 sentences", text)
                    self.assertIn("## Provenance", text)
                    self.assertNotIn('"pivotal"', text)
                    self.assertEqual(source.read_text(encoding="utf-8"), CORPUS)
                    self.assertEqual(protected.read_text(encoding="utf-8"), "Human-owned; unchanged.\n")


if __name__ == "__main__":
    unittest.main()
