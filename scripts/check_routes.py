#!/usr/bin/env python3
"""check_routes.py — deterministic structure & routing verifier for a skill package.

No LLM, no third-party dependencies. Checks:
  1. Reachability  — every route/link in SKILL.md and indexes resolves to a real
                     file (and #anchor) ; nothing dangles.
  2. Orphans       — every file under references/ scripts/ assets/ is reachable
                     from SKILL.md by following links.
  3. Compass cap   — SKILL.md <= 6000 chars.
  4. Conservation  — with --before <snapshot>, every substantive original line
                     still exists somewhere in the new doc set (split = verbatim
                     relocation; only headings / routing rows / blurbs may be new).

Usage:
  python3 check_routes.py <skill_dir>
  python3 check_routes.py <skill_dir> --before <snapshot_dir>

Exit 0 = clean, 1 = issues found.
"""

import argparse
import re
import sys
from pathlib import Path

COMPASS_CAP = 6000
SUPPORT_DIRS = ("references", "scripts", "assets")
SUPPORT_PREFIXES = tuple(d + "/" for d in SUPPORT_DIRS)
PATHLIKE_EXT = (".md", ".py", ".sh", ".json", ".txt", ".html", ".js", ".yaml", ".yml", ".csv")

FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
MDLINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
INLINE_CODE_RE = re.compile(r"`([^`]+)`")
HEADING_RE = re.compile(r"^#{1,6}\s+(.*)$")
TABLE_SEP_RE = re.compile(r"^\|?[\s:|-]+\|?$")


def strip_fences(text: str) -> str:
    return FENCE_RE.sub("", text)


def heading_slugs(text: str) -> set:
    slugs = set()
    for line in strip_fences(text).splitlines():
        m = HEADING_RE.match(line)
        if m:
            title = m.group(1).strip()
            slug = re.sub(r"[^\w\s-]", "", title.lower())
            slug = re.sub(r"\s+", "-", slug).strip("-")
            if slug:
                slugs.add(slug)
    return slugs


def has_placeholder(tok: str) -> bool:
    return any(c in tok for c in "*<>")


def extract_refs(text: str):
    """Path targets to treat as ROUTES from a markdown file.

    - Code fences are skipped (templates/examples, never real routes).
    - Inline-code paths count only when they carry a support-dir prefix
      (references/ scripts/ assets/); a bare filename in prose is a mention,
      not a route.
    - Markdown links are read from text OUTSIDE inline code, so a link shown as
      `[a](b)` to illustrate format is not treated as a route.
    - Placeholder/glob tokens (containing * < >) are ignored.
    """
    body = strip_fences(text)
    inline_spans = INLINE_CODE_RE.findall(body)
    body_no_code = INLINE_CODE_RE.sub(" ", body)
    refs = []
    for m in MDLINK_RE.finditer(body_no_code):
        t = m.group(1).strip()
        if t and not has_placeholder(t):
            refs.append(t)
    for span in inline_spans:
        for tok in span.split():
            tok = tok.strip()
            if not tok or has_placeholder(tok):
                continue
            base = tok.split("#", 1)[0]
            if base.startswith(SUPPORT_PREFIXES) and base.endswith(PATHLIKE_EXT):
                refs.append(tok)
    return refs


def split_anchor(raw: str):
    if "#" in raw:
        p, a = raw.split("#", 1)
        return p, a
    return raw, None


def is_ignorable_file(p: Path) -> bool:
    parts = p.parts
    if any(seg == "__pycache__" for seg in parts):
        return True
    if p.name.startswith("."):
        return True
    if p.suffix == ".pyc":
        return True
    return False


def walk_support_files(root: Path):
    files = []
    for d in SUPPORT_DIRS:
        base = root / d
        if not base.is_dir():
            continue
        for p in base.rglob("*"):
            if p.is_file() and not is_ignorable_file(p):
                files.append(p.resolve())
    return files


def check_reachability_and_orphans(root: Path):
    issues = []
    skill_md = root / "SKILL.md"
    reachable = set()
    queue = [skill_md.resolve()]
    seen_md = set()

    while queue:
        cur = queue.pop()
        if cur in seen_md:
            continue
        seen_md.add(cur)
        reachable.add(cur)
        # Only SKILL.md and index files carry routing responsibility. Dangling
        # links are reported against them; a broken path mentioned inside a
        # content reference is a mention, not a route, and is not flagged.
        is_router = (cur.name == "SKILL.md"
                     or cur.stem.lower() in ("index", "_index")
                     or cur.stem.lower().endswith("_index"))
        try:
            text = cur.read_text(encoding="utf-8")
        except Exception as e:
            issues.append(f"[read-error] {cur}: {e}")
            continue
        for raw in extract_refs(text):
            if raw.startswith(("http://", "https://", "mailto:")):
                continue
            path_part, anchor = split_anchor(raw)
            if path_part == "":
                if is_router and anchor and anchor.lower() not in heading_slugs(text):
                    issues.append(f"[dangling-anchor] {rel(cur, root)} -> #{anchor} (no such heading)")
                continue
            target = (cur.parent / path_part).resolve()
            if not target.exists():
                if is_router:
                    issues.append(f"[dangling] {rel(cur, root)} -> {raw} (file not found)")
                continue
            reachable.add(target)
            if is_router and anchor and target.suffix == ".md":
                slugs = heading_slugs(target.read_text(encoding="utf-8"))
                if anchor.lower() not in slugs:
                    issues.append(f"[dangling-anchor] {rel(cur, root)} -> {raw} (no such heading in target)")
            if target.suffix == ".md" and target not in seen_md:
                queue.append(target)

    # orphans: support files never reached
    for p in walk_support_files(root):
        if p not in reachable:
            issues.append(f"[orphan] {rel(p, root)} (not reachable from SKILL.md)")
    return issues


def rel(p: Path, root: Path) -> str:
    try:
        return str(Path(p).resolve().relative_to(root.resolve()))
    except ValueError:
        return str(p)


def check_compass(root: Path):
    issues = []
    skill_md = root / "SKILL.md"
    if not skill_md.exists():
        return [f"[missing] SKILL.md not found in {root}"]
    n = len(skill_md.read_text(encoding="utf-8"))
    status = "ok" if n <= COMPASS_CAP else "OVER"
    print(f"  SKILL.md = {n} chars (cap {COMPASS_CAP}) [{status}]")
    if n > COMPASS_CAP:
        issues.append(f"[compass-over] SKILL.md is {n} chars, over the {COMPASS_CAP} hard cap — demote content into references/")
    return issues


def substantive_lines(text: str):
    out = []
    for line in text.splitlines():
        s = line.strip()
        if not s or len(s) <= 3:
            continue
        if s.startswith("#"):
            continue
        if TABLE_SEP_RE.match(s):
            continue
        out.append(s)
    return out


def check_conservation(root: Path, before: Path):
    issues = []
    after_text = []
    for p in root.rglob("*.md"):
        if is_ignorable_file(p):
            continue
        try:
            after_text.append(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    after_lines = set()
    for blob in after_text:
        for ln in blob.splitlines():
            s = ln.strip()
            if s:
                after_lines.add(s)

    before_md = [p for p in before.rglob("*.md") if not is_ignorable_file(p)]
    if not before_md:
        issues.append(f"[conservation] no .md files found in snapshot {before}")
        return issues

    lost = 0
    for p in before_md:
        try:
            txt = p.read_text(encoding="utf-8")
        except Exception:
            continue
        for line in substantive_lines(txt):
            if line not in after_lines:  # exact full-line match (no substring false-negatives)
                issues.append(f"[lost-content] from {p.name}: {line[:80]!r}")
                lost += 1
    if lost == 0:
        print(f"  conservation: all substantive lines from {len(before_md)} snapshot doc(s) survive")
    return issues


def main():
    ap = argparse.ArgumentParser(description="Deterministic skill structure & routing checker")
    ap.add_argument("skill_dir", help="path to the skill package directory")
    ap.add_argument("--before", help="snapshot dir taken before restructuring (enables conservation check)")
    args = ap.parse_args()

    root = Path(args.skill_dir).resolve()
    if not (root / "SKILL.md").exists():
        print(f"ERROR: {root}/SKILL.md not found", file=sys.stderr)
        sys.exit(2)

    print(f"[check_routes] {root}")
    all_issues = []
    all_issues += check_compass(root)
    all_issues += check_reachability_and_orphans(root)
    if args.before:
        all_issues += check_conservation(root, Path(args.before).resolve())

    print()
    if not all_issues:
        print("[check_routes] PASS — no structural/routing issues")
        sys.exit(0)
    print(f"[check_routes] {len(all_issues)} issue(s):")
    for i in all_issues:
        print(f"  {i}")
    sys.exit(1)


if __name__ == "__main__":
    main()
