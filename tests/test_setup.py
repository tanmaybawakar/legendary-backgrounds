import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ReleaseChecks(unittest.TestCase):
    def test_install_keeps_references_and_existing_user_files(self):
        setup = load("lbg_setup", ROOT / "setup.py")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "legendary-backgrounds"
            (source / "assets/refs").mkdir(parents=True)
            (source / "assets/refs/example.jpg").write_bytes(b"reference")
            (source / "SKILL.md").write_text("skill")
            (source / ".DS_Store").write_text("private")
            python = root / ".venv" / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
            python.parent.mkdir(parents=True)
            python.touch()
            home = root / "home"
            with patch.object(setup, "__file__", str(root / "setup.py")), \
                    patch.object(setup.Path, "home", return_value=home), \
                    patch.object(sys, "argv", ["setup.py", "all"]), \
                    patch.object(setup.subprocess, "run") as run:
                setup.main()
                for agent in (".claude", ".agents", ".cursor"):
                    dest = home / agent / "skills/legendary-backgrounds"
                    self.assertEqual((dest / "assets/refs/example.jpg").read_bytes(), b"reference")
                    self.assertEqual((dest / "PYTHON_PATH.txt").read_text().strip(), str(python.resolve()))
                    self.assertFalse((dest / ".DS_Store").exists())
                    (dest / "my-notes.md").write_text("keep")
                setup.main()
                self.assertEqual((home / ".claude/skills/legendary-backgrounds/my-notes.md").read_text(), "keep")
                self.assertTrue(any("--preview" in call.args[0] for call in run.call_args_list))

    def test_image_helper_does_not_pick_up_unrelated_codex_images(self):
        helper = load("lbg_image", ROOT / "legendary-backgrounds/scripts/codex_image.py")
        from PIL import Image
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            work = root / "work"
            work.mkdir()
            shared = root / "codex/generated_images"
            shared.mkdir(parents=True)
            Image.new("RGB", (8, 8)).save(shared / "private.png")
            output = root / "result.png"
            with patch.object(sys, "argv", ["codex_image.py", "--prompt", "test", "--out", str(output)]), \
                    patch.object(helper.shutil, "which", return_value="codex"), \
                    patch.object(helper.tempfile, "mkdtemp", return_value=str(work)), \
                    patch.dict(helper.os.environ, {"CODEX_HOME": str(root / "codex")}), \
                    patch.object(helper.subprocess, "run", side_effect=[
                        subprocess.CompletedProcess([], 0, "Logged in", ""),
                        subprocess.CompletedProcess([], 0, "", "")]):
                with self.assertRaises(SystemExit) as error:
                    helper.main()
                self.assertEqual(error.exception.code, 6)
                self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
