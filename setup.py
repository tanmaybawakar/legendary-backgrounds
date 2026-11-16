#!/usr/bin/env python3
"""Install the complete skill, its Python environment, and verify a first render."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import venv


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("agent", nargs="?", default="all",
                        choices=("all", "claude", "codex", "cursor", "agents"))
    args = parser.parse_args()
    if sys.version_info < (3, 10):
        parser.error("Python 3.10 or newer is required.")
    root = Path(__file__).resolve().parent
    source = root / "legendary-backgrounds"
    env = root / ".venv"
    python = env / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    if not python.exists():
        print("Creating an isolated Python environment...", flush=True)
        venv.EnvBuilder(with_pip=True).create(env)
    subprocess.run([str(python), "-m", "pip", "install", "--disable-pip-version-check",
                    "-r", str(source / "requirements.txt")], check=True)
    home = Path.home()
    destinations = {"claude": home / ".claude/skills", "codex": home / ".agents/skills",
                    "cursor": home / ".cursor/skills", "agents": home / ".agents/skills"}
    agents = ("claude", "codex", "cursor") if args.agent == "all" else (args.agent,)
    for agent in agents:
        destination = destinations[agent] / "legendary-backgrounds"
        if destination.resolve() != source.resolve():
            shutil.copytree(source, destination, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns(".DS_Store", "._*", ".claude",
                                                         "__pycache__", ".venv", "PYTHON_PATH.txt"))
        (destination / "PYTHON_PATH.txt").write_text(str(python) + "\n", encoding="utf-8")
        print(f"Installed for {agent}: {destination}", flush=True)
    output = root / ".legendary-backgrounds/setup-preview.jpg"
    output.parent.mkdir(exist_ok=True)
    subprocess.run([str(python), str(source / "scripts/render.py"),
                    str(source / "presets/nova-arc.json"), "--preview", str(output),
                    "--size", "640x400"], check=True)
    print(f"Ready. First render: {output}")
    print("Restart your agent if needed, then ask: Use legendary-backgrounds for my landing page.")
    print("Keep this downloaded folder: installed skills use its .venv interpreter.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, subprocess.CalledProcessError) as error:
        print(f"Setup failed: {error}", file=sys.stderr)
        sys.exit(1)
