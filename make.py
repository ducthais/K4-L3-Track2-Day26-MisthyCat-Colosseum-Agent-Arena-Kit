#!/usr/bin/env python3
"""Cross-platform runner for COLOSSEUM kit Makefile targets.
Enables running `make <target>` directly on Windows, macOS, and Linux.
"""

import glob
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def get_python_bin():
    if os.name == "nt":
        scripts_bin = ROOT / ".venv" / "Scripts" / "python.exe"
        if scripts_bin.is_file():
            return str(scripts_bin)
    else:
        unix_bin = ROOT / ".venv" / "bin" / "python"
        if unix_bin.is_file():
            return str(unix_bin)
    return sys.executable

def get_pytest_bin():
    if os.name == "nt":
        scripts_bin = ROOT / ".venv" / "Scripts" / "pytest.exe"
        if scripts_bin.is_file():
            return str(scripts_bin)
    else:
        unix_bin = ROOT / ".venv" / "bin" / "pytest"
        if unix_bin.is_file():
            return str(unix_bin)
    return "pytest"

def run_cmd(cmd, check=True, cwd=str(ROOT)):
    if isinstance(cmd, list):
        res = subprocess.run(cmd, cwd=cwd)
    else:
        res = subprocess.run(cmd, shell=True, cwd=cwd)
    if check and res.returncode != 0:
        sys.exit(res.returncode)
    return res

def parse_args():
    target = "doctor"
    kwargs = {}
    args = sys.argv[1:]
    if args and not args[0].startswith("-") and "=" not in args[0]:
        target = args[0]
        args = args[1:]
    
    for a in args:
        if "=" in a:
            k, v = a.split("=", 1)
            kwargs[k.upper()] = v
        elif a.startswith("--"):
            parts = a[2:].split("=", 1)
            if len(parts) == 2:
                kwargs[parts[0].upper()] = parts[1]
            else:
                kwargs[parts[0].upper()] = True
    return target, kwargs

def target_install():
    print("Setting up virtual environment with Python 3.12...")
    uv = shutil.which("uv")
    venv_dir = ROOT / ".venv"
    if uv:
        run_cmd([uv, "venv", "--python", "3.12", "--seed", str(venv_dir)])
    else:
        run_cmd([sys.executable, "-m", "venv", str(venv_dir)])
    
    py = get_python_bin()
    run_cmd([py, "-m", "pip", "install", "-q", "--upgrade", "pip"])
    run_cmd([py, "-m", "pip", "install", "-q", "pytest"])
    print("ready. no api key needed, ever.")

def target_check_no_key():
    py = get_python_bin()
    run_cmd([py, "-m", "kit.gate_no_key"])

def target_check_world():
    manifests = sorted(glob.glob(str(ROOT / "kit" / "world" / "*" / "manifest.json")))
    if not manifests:
        print("no world in kit/world/ - ask your instructor for the world artifact")
        sys.exit(1)
    
    with open(manifests[-1], "r", encoding="utf-8") as f:
        m = json.load(f)
    world_id = m.get("world_id")
    counts = m.get("counts", {})
    # manifest may include __total__; if so, count total pages
    total_pages = counts.get("__total__", sum(counts.values()))
    print(f"world {world_id} - {total_pages} pages")

    truths = glob.glob(str(ROOT / "kit" / "world" / "*" / "truth.json"))
    if truths:
        print("FAIL: truth.json must never ship to students")
        sys.exit(1)

def target_check_referee():
    referee_dir = ROOT / "kit" / "referee"
    if not referee_dir.is_dir():
        print("kit/referee missing - ask your instructor to run tools.sync_referee")
        sys.exit(1)
    py = get_python_bin()
    code = (
        "from kit.referee.rubric import CLASSES; "
        "from kit.referee.adjudicate import LOCAL_ONLY; "
        "print(f'referee: {len(CLASSES)} classes, local_only={LOCAL_ONLY}')"
    )
    run_cmd([py, "-c", code])

def get_world_dir():
    manifests = sorted(glob.glob(str(ROOT / "kit" / "world" / "*" / "manifest.json")))
    if not manifests:
        print("no world exported - run 'make check-world'")
        sys.exit(1)
    return str(Path(manifests[0]).parent)

def target_validate():
    world_dir = get_world_dir()
    py = get_python_bin()
    run_cmd([
        py,
        str(ROOT / "validate_deck.py"),
        str(ROOT / "deck" / "deck.json"),
        str(ROOT / "deck" / "lineup.json"),
        "--world",
        world_dir,
    ])

def target_validate_bots():
    world_dir = get_world_dir()
    py = get_python_bin()
    for b in ["rookie", "operator", "adversary"]:
        print(f"{b:<12} ", end="", flush=True)
        res = subprocess.run(
            [
                py,
                str(ROOT / "validate_deck.py"),
                str(ROOT / "bots" / b / "deck.json"),
                str(ROOT / "bots" / b / "lineup.json"),
                "--world",
                world_dir,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(ROOT),
        )
        lines = [line.strip() for line in res.stdout.strip().splitlines() if line.strip()]
        last_line = lines[-1] if lines else ""
        print(last_line)

def target_doctor():
    target_check_no_key()
    target_check_world()
    target_check_referee()
    target_validate()
    print("ready to spar.")

def target_spar(kwargs):
    bot = kwargs.get("BOT", "rookie")
    role = kwargs.get("AS", kwargs.get("ROLE", "all"))
    py = get_python_bin()
    run_cmd([py, str(ROOT / "spar.py"), "--bot", str(bot), "--as", str(role)])

def target_ui():
    py = get_python_bin()
    run_cmd([py, "-m", "kit.arena_ui.build_ui"])
    run_cmd([py, "-m", "kit.arena_ui.serve", "--open"])

def target_test():
    target_check_no_key()
    py = get_python_bin()
    run_cmd([py, "-m", "pytest", "tests/"])

def target_submit(kwargs):
    target_validate()
    team = kwargs.get("TEAM")
    if not team:
        print("usage: make submit TEAM=<your-team-name>")
        sys.exit(1)
    py = get_python_bin()
    run_cmd([py, "-m", "kit.submit", "--team", str(team)])

def target_clean():
    for p in ROOT.rglob("__pycache__"):
        if p.is_dir():
            shutil.rmtree(p, ignore_errors=True)
    pytest_cache = ROOT / ".pytest_cache"
    if pytest_cache.is_dir():
        shutil.rmtree(pytest_cache, ignore_errors=True)
    print("cleaned.")

def main():
    target, kwargs = parse_args()
    targets = {
        "install": target_install,
        "doctor": target_doctor,
        "check-no-key": target_check_no_key,
        "check-world": target_check_world,
        "check-referee": target_check_referee,
        "validate": target_validate,
        "validate-bots": target_validate_bots,
        "spar": lambda: target_spar(kwargs),
        "ui": target_ui,
        "test": target_test,
        "submit": lambda: target_submit(kwargs),
        "clean": target_clean,
    }
    
    if target in targets:
        targets[target]()
    else:
        print(f"Unknown target: {target}")
        print(f"Available targets: {', '.join(targets.keys())}")
        sys.exit(1)

if __name__ == "__main__":
    main()
