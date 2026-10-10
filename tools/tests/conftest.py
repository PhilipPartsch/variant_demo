"""Shared fixtures of the CV platform tests (T§).

Levels (T§1): L1 tooling unit, L2 build integration, L3 docs per product,
L4 content, L5 negative / mutation, L6 C code. L3, L4 and L6 read the outputs
of `tools/build_all.sh` in build/site/<product>/ (tools/test_all.sh runs it
first); L2 and L5 build into temporary directories.
"""
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "build" / "site"
D, N, B, A = "truck_diesel_eu", "truck_bev_nmc_eu", "bus_bev_lfp_eu", "truck_bev_lfp_na"
PRODUCTS = (D, N, B, A)
BEV = (N, B, A)


def ubc_path() -> str:
    if os.environ.get("UBC"):
        return os.environ["UBC"]
    found = sorted(Path.home().glob(".vscode/extensions/useblocks.ubcode-*/server/cli/ubc"))
    return str(found[-1]) if found else shutil.which("ubc")


UBC = ubc_path()
PYTHON = str(ROOT / ".venv/bin/python") if (ROOT / ".venv/bin/python").exists() else shutil.which("python3")
SPHINX = str(ROOT / ".venv/bin/sphinx-build") if (ROOT / ".venv/bin/sphinx-build").exists() else shutil.which("sphinx-build")


def run(cmd, cwd=ROOT, check=False, env=None):
    """Run a command, return CompletedProcess with combined output in .out."""
    e = dict(os.environ, PATH=f"{Path(PYTHON).parent}:{os.environ['PATH']}", **(env or {}))
    p = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=e)
    p.out = p.stdout
    if check and p.returncode:
        raise AssertionError(f"{' '.join(map(str, cmd))} failed ({p.returncode}):\n{p.out[-3000:]}")
    return p


def load_needs(path: Path) -> dict:
    d = json.loads(path.read_text())
    v = d["versions"]
    return v[d.get("current_version") or next(iter(v))]["needs"]


@pytest.fixture(scope="session")
def site():
    """needs per product and tool from the last tools/build_all.sh run."""
    missing = [p for p in PRODUCTS if not (SITE / p / "ubc.needs.json").exists()]
    if missing:
        pytest.skip(f"no build outputs for {missing}: run tools/build_all.sh (or tools/test_all.sh)")
    return {p: {t: load_needs(SITE / p / f"{t}.needs.json") for t in ("ubc", "sphinx")} for p in PRODUCTS}


def local(needs: dict) -> dict:
    return {i: n for i, n in needs.items() if not i.startswith("BMS_")}


EVIDENCE = ("test_result", "gap")


def authored(needs: dict) -> dict:
    """Without the generated evidence (test results, workflow gaps)."""
    return {i: n for i, n in needs.items() if n["type"] not in EVIDENCE}


class Repo:
    """A throw-away copy of the working tree (a git repository of its own, so
    sphinx-codelinks finds a loose ref and the origin URL)."""

    def __init__(self, path: Path):
        self.path = path

    def file(self, rel: str) -> Path:
        return self.path / rel

    def edit(self, rel: str, old: str, new: str, count: int = 1):
        f = self.file(rel)
        s = f.read_text()
        assert old in s, f"{rel}: {old!r} not found"
        f.write_text(s.replace(old, new, count))

    def append(self, rel: str, text: str):
        with self.file(rel).open("a") as fh:
            fh.write(text)

    def configure(self, product: str):
        run(["cmake", "-S", ".", "-B", f"build/cmake/{product}", "-G", "Ninja", f"-DVARIANT={product}"], cwd=self.path, check=True)
        run(["cmake", "--build", f"build/cmake/{product}"], cwd=self.path, check=True)
        shutil.copy(self.path / f"build/cmake/{product}/compile_commands.json", self.path / "build/compile_commands.json")

    def ubc_check(self):
        return run([UBC, "check"], cwd=self.path)

    def sphinx(self, warnings_as_errors=True):
        cmd = [SPHINX, "-E", "-q", "-b", "html", "docs", "build/sphinx"]
        if warnings_as_errors:
            cmd[1:1] = ["-W", "--keep-going"]
        return run(cmd, cwd=self.path)

    def tool(self, *args):
        return run([PYTHON, *args], cwd=self.path)


def make_repo(tmp_path: Path) -> Repo:
    files = run(["git", "ls-files", "-co", "--exclude-standard"], check=True).out.split()
    dst = tmp_path / "repo"
    for rel in files:
        src = ROOT / rel
        if src.is_file():
            (dst / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst / rel)
    run(["git", "init", "-q"], cwd=dst, check=True)
    run(["git", "add", "-A"], cwd=dst, check=True)
    run(["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid", "commit", "-q", "-m", "copy"], cwd=dst, check=True)
    run(["git", "remote", "add", "origin", "https://github.com/PhilipPartsch/variant_demo"], cwd=dst, check=True)
    return Repo(dst)


@pytest.fixture
def repo(tmp_path):
    return make_repo(tmp_path)
