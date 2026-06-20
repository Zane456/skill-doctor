#!/usr/bin/env python3
"""check_desc_slim.py — deterministic gate for description slimming (deletion-only).

Slimming a skill description risks silently cutting a trigger word the user types.
This gate makes slimming safe WITHOUT per-skill user confirmation by enforcing:

  1. DELETION-ONLY: every sentence kept in NEW must be a verbatim substring of OLD
     (whitespace-normalized). No rewrites, no paraphrasing, no new words.
  2. PROTECTED SPANS survive: every backticked span, quoted span ("…" '…' 「…」),
     the literal phrase "ALWAYS invoke", and every comma-separated token of a
     "Triggers:"/"触发" list segment in OLD must still be present in NEW.

Usage:
  python3 check_desc_slim.py <old_SKILL.md_or_backup> <new_SKILL.md>

Exit 0 = slim is safe (prints removed sentences as a log).
Exit 1 = VIOLATION (rewrite detected, or a protected trigger span was cut) — do not keep the new file.
Exit 2 = cannot read/parse inputs.
"""
import re
import sys
from pathlib import Path

DESC_RE = re.compile(r"^description:\s*(.*?)(?=^[A-Za-z_-]+:|^---\s*$)", re.S | re.M)


def read_desc(md_file: Path) -> str | None:
    try:
        text = md_file.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    if not m:
        return None
    d = DESC_RE.search(m.group(1) + "\n---")
    if not d:
        return None
    val = d.group(1).strip()
    if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
        val = val[1:-1]
    return re.sub(r"\s+", " ", val).strip()


def sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?。！？;；])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def protected_spans(old: str) -> list[str]:
    spans: list[str] = []
    spans += re.findall(r"`([^`]+)`", old)
    spans += re.findall(r"\"([^\"]{2,})\"", old)
    spans += re.findall(r"'([^']{3,})'", old)
    spans += re.findall(r"「([^」]+)」", old)
    if re.search(r"ALWAYS invoke", old, re.I):
        spans.append("ALWAYS invoke")
    # Trigger list segment: from "Triggers:" / "触发(词)" up to sentence end
    for m in re.finditer(r"(?:Triggers?|触发[词on]*)\s*[:：]([^.。!！?？]*)", old, re.I):
        for tok in re.split(r"[,，、/]", m.group(1)):
            tok = tok.strip().strip("'\"")
            if len(tok) >= 2:
                spans.append(tok)
    # dedupe, keep order
    seen, out = set(), []
    for s in spans:
        s = re.sub(r"\s+", " ", s).strip()
        if s and s.lower() not in seen:
            seen.add(s.lower())
            out.append(s)
    return out


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    old_p, new_p = Path(sys.argv[1]), Path(sys.argv[2])
    old, new = read_desc(old_p), read_desc(new_p)
    if old is None or new is None:
        print(f"ERROR: cannot extract description from {'OLD' if old is None else 'NEW'} file")
        return 2

    violations: list[str] = []

    # 1. deletion-only: every NEW sentence verbatim in OLD
    for s in sentences(new):
        if s not in old:
            violations.append(f"[rewrite] NEW sentence is not verbatim from OLD: {s[:90]!r}")

    # 2. protected spans survive
    for span in protected_spans(old):
        if span.lower() not in new.lower():
            violations.append(f"[trigger-cut] protected span removed: {span!r}")

    removed = [s for s in sentences(old) if s not in new]

    print(f"[check_desc_slim] old={len(old)} chars -> new={len(new)} chars  (-{len(old) - len(new)})")
    if removed:
        print(f"removed sentences ({len(removed)}):")
        for s in removed:
            print(f"  - {s[:100]}")
    if violations:
        print(f"\nFAIL — {len(violations)} violation(s), restore the old description:")
        for v in violations:
            print(f"  {v}")
        return 1
    print("\nPASS — deletion-only, all trigger spans intact")
    return 0


if __name__ == "__main__":
    sys.exit(main())
