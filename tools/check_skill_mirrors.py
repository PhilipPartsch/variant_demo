"""Check that every skill exists identically in the three host locations.

.claude/skills/<name>/SKILL.md   (Claude Code; the copy `ubc agent doctor` checks)
.agents/skills/<name>/SKILL.md   (agents-standard hosts)
.github/agents/<name>.agent.md   (GitHub Copilot)

`ubc agent doctor` only checks mirrors of skills in its install manifest, so
project-specific skills (e.g. draft-allocation) need this check.
"""
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
names = {p.parent.name for p in root.glob(".claude/skills/*/SKILL.md")}
names |= {p.parent.name for p in root.glob(".agents/skills/*/SKILL.md")}
names |= {p.name.removesuffix(".agent.md") for p in root.glob(".github/agents/*.agent.md")}
host_only = {"workflow-author"}  # shipped by the ubc profile for GitHub only
bad = 0
for n in sorted(names - host_only):
    copies = [root / f".claude/skills/{n}/SKILL.md", root / f".agents/skills/{n}/SKILL.md", root / f".github/agents/{n}.agent.md"]
    texts = [c.read_text() if c.exists() else None for c in copies]
    if None in texts or len(set(texts)) != 1:
        bad += 1
        state = ", ".join(f"{c.relative_to(root)}: {'missing' if t is None else 'differs' if t != texts[0] else 'ok'}" for c, t in zip(copies, texts))
        print(f"skill {n}: {state}")
print(f"{len(names - host_only)} skills checked, {bad} out of sync")
sys.exit(1 if bad else 0)
