"""Assemble the published site from the product builds (A§3).

Usage:
  make_site.py [--src build/site] [--out build/site]

Reads build/site/<product>/ (written by tools/build_product.sh: sphinx/,
ubcode/, ubc.needs.json, sphinx.needs.json, junit.xml) and writes the tree that
is published on the gh-pages branch:

  index.html, products.json, assets/site.css, .nojekyll
  <product>/sphinx/, ubcode/, compare.html, needs-diff.html,
            needs.sphinx.json, needs.ubc.json, tests/index.html

With --out different from --src (CI: the gh-pages working copy), every variant
folder is replaced completely and folders of products without a defconfig are
removed. Build-local files (.doctrees, logs, gaps.json, junit.xml) are not
published. Absolute local paths (ubc `__source__`, codelinks `local-url`; plan 99
UB-01, UB-14, CL-03) are rewritten to repository-relative paths; the run fails
if a `file://` path or the repository path is left.
"""
import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools/tests"))
from normalize import normalize  # noqa: E402

SKIP = {".doctrees", ".buildinfo", "logs"}
CSS = """
body{font-family:system-ui,-apple-system,Segoe UI,sans-serif;margin:0;color:#1f2328;background:#fff}
header{padding:16px 24px;border-bottom:1px solid #d0d7de}
h1{font-size:20px;margin:0 0 4px} .meta{color:#59636e;font-size:13px}
main{padding:16px 24px} table{border-collapse:collapse;font-size:14px}
th,td{border:1px solid #d0d7de;padding:6px 10px;text-align:left;vertical-align:top}
th{background:#f6f8fa} a{color:#0969da} .ok{color:#1a7f37} .bad{color:#cf222e}
.bar{display:flex;gap:12px;align-items:center;padding:8px 16px;border-bottom:1px solid #d0d7de;flex-wrap:wrap}
.panes{display:grid;grid-template-columns:1fr 1fr;height:calc(100vh - 50px)}
.panes iframe{width:100%;height:100%;border:0;border-right:1px solid #d0d7de}
.pane-title{font-weight:600}
@media (prefers-color-scheme:dark){body{background:#0d1117;color:#e6edf3}th{background:#161b22}
th,td,header,.bar{border-color:#30363d}.meta{color:#9198a1}a{color:#4493f8}}
@media (max-width:800px){.panes{grid-template-columns:1fr;grid-template-rows:1fr 1fr}}
"""


def needs_of(path: Path) -> dict:
    d = json.loads(path.read_text())
    v = d["versions"]
    return v[d.get("current_version") or next(iter(v))]["needs"]


def products() -> list[str]:
    return sorted(p.name.removesuffix("_defconfig") for p in (ROOT / "configs").glob("*_defconfig"))


def describe(product: str) -> str:
    d = json.loads((ROOT / f"variants/{product}.json").read_text())
    parts = [d["vehicle"]["type"], d["powertrain"]["type"].upper() if d["powertrain"]["type"] == "bev" else "diesel"]
    if d["bms"]["enabled"]:
        parts += [d["bms"]["chemistry"].upper(), d["hv"]["voltage"].removeprefix("v") + " V"]
    parts += [f for f in ("MCS", "pantograph") if d["charging"][f.lower()]]
    parts.append(d["market"]["region"].upper())
    return " · ".join(parts)


def copy_product(src: Path, dst: Path):
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    for name in ("sphinx", "ubcode"):
        shutil.copytree(src / name, dst / name, ignore=shutil.ignore_patterns(*SKIP))
    shutil.copy(src / "sphinx.needs.json", dst / "needs.sphinx.json")
    shutil.copy(src / "ubc.needs.json", dst / "needs.ubc.json")


def strip_local_paths(folder: Path, repo_roots: list[str]) -> int:
    """Make paths of the build machine repository-relative: `file:///<repo>/x#Lnn`
    and `<repo>/x` become `x` (plan 99 UB-01 `__source__`, UB-14, CL-03)."""
    pattern = re.compile(r"(?:file://)?(?:" + "|".join(re.escape(r.rstrip("/")) for r in repo_roots) + r")/")
    changed = 0
    for f in list(folder.rglob("*.html")) + list(folder.glob("needs.*.json")):
        text = f.read_text(errors="ignore")
        new = pattern.sub("", text)
        if new != text:
            f.write_text(new)
            changed += 1
    return changed


def needs_diff(dst: Path) -> tuple[int, str]:
    u, s = needs_of(dst / "needs.ubc.json"), needs_of(dst / "needs.sphinx.json")
    rows = [(i, "only in ubc", "") for i in sorted(set(u) - set(s))]
    rows += [(i, "only in Sphinx", "") for i in sorted(set(s) - set(u))]
    for i in sorted(set(u) & set(s)):
        keys = set(u[i]) & set(s[i])
        a, b = normalize(u[i], keys), normalize(s[i], keys)
        for k in sorted(set(a) | set(b)):
            if a.get(k) != b.get(k):
                rows.append((i, k, f"ubc: {a.get(k)!r} / Sphinx: {b.get(k)!r}"))
    body = "".join(f"<tr><td>{html.escape(i)}</td><td>{html.escape(k)}</td><td>{html.escape(v)}</td></tr>" for i, k, v in rows)
    table = (f"<table><tr><th>Need</th><th>Difference</th><th>Values</th></tr>{body}</table>" if rows
             else "<p class='ok'>No differences: ubc and Sphinx export the same needs (after normalisation of the known export differences).</p>")
    return len(rows), table


def tests_page(src: Path, dst: Path) -> tuple[int, int]:
    rows, passed, total = [], 0, 0
    junit = src / "junit.xml"
    if junit.exists():
        for case in ET.parse(junit).getroot().iter("testcase"):
            for outcome, test_id in re.findall(r"^(PASS|FAIL) (TEST_\w+)$", case.findtext("system-out") or "", re.M):
                total += 1
                passed += outcome == "PASS"
                cls = "ok" if outcome == "PASS" else "bad"
                rows.append(f"<tr><td>{case.get('name')}</td><td>{test_id}</td><td class='{cls}'>{outcome}</td></tr>")
    (dst / "tests").mkdir(exist_ok=True)
    page(dst / "tests/index.html", f"Tests — {dst.name}", "../../",
         f"<p>{passed} of {total} passed (CTest).</p><table><tr><th>Executable</th><th>Test</th><th>Result</th></tr>{''.join(rows)}</table>")
    return passed, total


def page(path: Path, title: str, prefix: str, body: str, header: str = ""):
    path.write_text(f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title>
<link rel="stylesheet" href="{prefix}assets/site.css"></head><body>
<header><h1>{html.escape(title)}</h1>{header}<div class="meta"><a href="{prefix}index.html">all products</a></div></header>
<main>{body}</main></body></html>
""")


def compare_page(dst: Path, all_products: list[str]):
    common = sorted(
        p.relative_to(dst / "sphinx").as_posix()
        for p in (dst / "sphinx").rglob("*.html")
        if not p.relative_to(dst / "sphinx").parts[0].startswith("_")
        and (dst / "ubcode" / p.relative_to(dst / "sphinx")).exists()
    )
    common.sort(key=lambda x: (x != "index.html", x))
    options = "".join(f'<option value="{p}">{p.removesuffix(".html")}</option>' for p in common)
    product_opts = "".join(f'<option value="{p}"{" selected" if p == dst.name else ""}>{p}</option>' for p in all_products)
    (dst / "compare.html").write_text(f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{dst.name} — sphinx-needs and ubCode</title>
<link rel="stylesheet" href="../assets/site.css"></head><body>
<div class="bar"><a href="../index.html">all products</a>
<label>Product <select id="product">{product_opts}</select></label>
<label>Page <select id="page">{options}</select></label>
<span class="pane-title">left: sphinx-needs · right: ubCode</span>
<a id="open-s" href="sphinx/index.html" target="_blank">open sphinx-needs</a>
<a id="open-u" href="ubcode/index.html" target="_blank">open ubCode</a></div>
<div class="panes"><iframe id="s" src="sphinx/index.html" title="sphinx-needs"></iframe>
<iframe id="u" src="ubcode/index.html" title="ubCode"></iframe></div>
<script>
const page = document.getElementById('page');
function show(p) {{ for (const [f, d] of [['s','sphinx'],['u','ubcode']]) {{
  document.getElementById(f).src = d + '/' + p; document.getElementById('open-' + f).href = d + '/' + p; }}
  history.replaceState(null, '', '#' + p); }}
page.addEventListener('change', () => show(page.value));
document.getElementById('product').addEventListener('change', e =>
  location.href = '../' + e.target.value + '/compare.html#' + page.value);
const start = decodeURIComponent(location.hash.slice(1));
if (start && [...page.options].some(o => o.value === start)) {{ page.value = start; show(start); }}
</script></body></html>
""")


def tool_versions() -> dict:
    out = {}
    try:
        from importlib.metadata import version
        for pkg in ("sphinx", "sphinx-needs", "sphinx-mounts", "sphinx-codelinks"):
            out[pkg] = version(pkg)
    except Exception:  # noqa: BLE001 - versions are informational
        pass
    bundled = sorted(Path.home().glob(".vscode/extensions/useblocks.ubcode-*/server/cli/ubc"))  # as tools/env.sh
    ubc = os.environ.get("UBC") or (str(bundled[-1]) if bundled else shutil.which("ubc"))
    if ubc:
        try:
            out["ubc"] = subprocess.run([ubc, "--version"], capture_output=True, text=True).stdout.split()[-1]
        except Exception:  # noqa: BLE001
            pass
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--src", type=Path, default=ROOT / "build/site")
    ap.add_argument("--out", type=Path, default=None, help="default: same as --src")
    ap.add_argument("--repo-root", action="append", default=[], help="absolute repo path(s) to strip from local URLs")
    args = ap.parse_args()
    src, out = args.src.resolve(), (args.out or args.src).resolve()
    out.mkdir(parents=True, exist_ok=True)
    roots = args.repo_root or [str(ROOT)]
    prods = products()

    previous = json.loads((out / "products.json").read_text())["products"] if (out / "products.json").exists() else []
    for old in previous:
        if old["name"] not in prods and (out / old["name"]).is_dir():
            shutil.rmtree(out / old["name"])

    (out / "assets").mkdir(exist_ok=True)
    (out / "assets/site.css").write_text(CSS.strip() + "\n")
    (out / ".nojekyll").write_text("")
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    built = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    versions = tool_versions()
    bms = re.search(r'CV_BMS_VERSION "([^"]+)"', (ROOT / "cmake/bms.cmake").read_text()).group(1)

    manifest, rows = [], []
    for p in prods:
        if not (src / p / "sphinx/index.html").exists():
            print(f"make_site: {p}: no build in {src / p} — skipped", file=sys.stderr)
            continue
        dst = out / p
        if dst != src / p:
            copy_product(src / p, dst)
        else:
            for name, target in (("sphinx.needs.json", "needs.sphinx.json"), ("ubc.needs.json", "needs.ubc.json")):
                shutil.copy(src / p / name, dst / target)
        strip_local_paths(dst, roots)
        n_diff, diff_table = needs_diff(dst)
        page(dst / "needs-diff.html", f"Needs diff ubc ↔ Sphinx — {p}", "../", diff_table)
        passed, total = tests_page(src / p, dst)
        compare_page(dst, prods)
        manifest.append({"name": p, "configuration": describe(p), "needs_diff": n_diff, "tests": [passed, total]})
        diff_cell = "<span class='ok'>✓ identical</span>" if n_diff == 0 else f"<span class='bad'>{n_diff} differences</span>"
        test_cls = "ok" if passed == total and total else "bad"
        rows.append(f"<tr><td><code>{p}</code></td><td>{describe(p)}</td>"
                    f"<td><a href='{p}/sphinx/index.html'>sphinx-needs</a></td><td><a href='{p}/ubcode/index.html'>ubCode</a></td>"
                    f"<td><a href='{p}/compare.html'>side by side</a></td><td><a href='{p}/needs-diff.html'>{diff_cell}</a></td>"
                    f"<td><a href='{p}/tests/index.html' class='{test_cls}'>{passed}/{total}</a></td></tr>")

    build_only = {"ubc.needs.json", "sphinx.needs.json", "gaps.json", "junit.xml"}
    published = [f for f in out.rglob("*") if f.is_file() and f.suffix in (".html", ".json")
                 and f.name not in build_only and not SKIP & set(f.relative_to(out).parts)]
    markers = ["file:///", *roots]
    left = [str(f) for f in published if any(m in f.read_text(errors="ignore") for m in markers)]
    if left:
        print("make_site: local paths left in:\n  " + "\n  ".join(left), file=sys.stderr)
        return 1

    tools = " · ".join(f"{k} {v}" for k, v in versions.items())
    header = f"<div class='meta'>commit <code>{commit[:12]}</code> · built {built} · BMS {bms} · {html.escape(tools)}</div>"
    page(out / "index.html", "CV platform — variant documentation", "",
         "<p>One documentation source, four products, two toolchains. Each product is built with "
         "<b>sphinx-needs</b> and with <b>ubCode</b>; open both side by side to compare.</p>"
         "<table><tr><th>Product</th><th>Configuration</th><th colspan=2>Documentation</th><th>Compare</th>"
         f"<th>Needs ubc ↔ Sphinx</th><th>Tests</th></tr>{''.join(rows)}</table>", header)
    (out / "products.json").write_text(json.dumps(
        {"commit": commit, "built": built, "bms": bms, "tools": versions, "products": manifest}, indent=2) + "\n")
    print(f"make_site: {len(manifest)} products → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
