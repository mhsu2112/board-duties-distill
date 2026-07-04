#!/usr/bin/env python3
"""Relative-reference checker. A reference resolves if it exists relative to the
referencing file's directory, ANY of its ancestor directories (authors often wrote
paths relative to a component root like boarddistill/), or the repo root.
Historical references that intentionally describe past layouts are allowlisted."""
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {'.git','.venv','node_modules','__pycache__','.mypy_cache','.ruff_cache','.pytest_cache','_archive','.claude'}
md_link = re.compile(r'\]\(([^)#\s]+)')
tick_path = re.compile(r'`([A-Za-z0-9_\-./ ]+\.(?:md|json|xlsx|docx|html|png|svg|csv|py|pdf))`')

ALLOWLIST = {
  # Stage-1 eval instructions describe the judge-session working layout used during the
  # 2026-06 runs; outputs were archived under Evals/. Historical, intentionally unchanged.
  ('Tools/sludge-report-evaluation-instructions.md', None),
  # PRD 'parent projects' table names the folders as prose, not as links.
  ('boarddistill-prd-v0.1.md', 'bank boards_cumulative-sludge/README.md'),
  # Engine AGENTS files are build SPECS for a repo not yet constructed (criminal profile):
  # their paths describe the target layout, intentionally.
  ('statute-distill_lex-allium/AGENTS.md', None),
  ('boarddistill/specs/statutedistill-AGENTS.md', None),
}
def allowed(src, ref):
    return (src, ref) in ALLOWLIST or (src, None) in ALLOWLIST

def files():
    for p in ROOT.rglob('*.md'):
        if not any(part in SKIP_DIRS for part in p.parts): yield p

broken = []
for f in files():
    text = f.read_text(errors='ignore')
    refs = set()
    for m in md_link.finditer(text):
        t = m.group(1)
        if not t.startswith(('http://','https://','mailto:')): refs.add(t)
    for m in tick_path.finditer(text):
        t = m.group(1)
        if '/' in t: refs.add(t)
    bases = [f.parent] + list(f.parents) + [ROOT, ROOT/'boarddistill']
    for r in refs:
        ok = False
        for b in bases:
            try:
                c = (b / r).resolve()
                if c.exists() and str(c).startswith(str(ROOT)): ok = True; break
            except Exception: pass
        if not ok and not allowed(str(f.relative_to(ROOT)), r):
            broken.append((str(f.relative_to(ROOT)), r))
if broken:
    print(f"BROKEN ({len(broken)}):")
    for src, ref in sorted(broken): print(f"  {src}  ->  {ref}")
    sys.exit(1)
print("All relative references resolve (allowlist:", len(ALLOWLIST), "historical entries).")
