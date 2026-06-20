#!/usr/bin/env python3
"""check_listing_budget.py — sum installed skill descriptions vs the platform's
skill-listing budget, across Claude Code / Codex / Hermes / OpenClaw.

Every one of these platforms injects each skill's name+description into the system
prompt under a budget and degrades on overflow. A description dropped/shortened
out of the listing can't auto-trigger. This script measures the population so
skill-doctor can judge one skill in the crowd it competes with.

Platform is auto-detected (see detect_platform.py); the per-platform budget
constants (fraction / fixed chars / cap / snapshot) come from there — this file
only consumes them. Pass --platform <name> to force one when several are installed.
  claude_code : fraction (skillListingBudgetFraction, default 1%) x context.
  codex       : ~2% of context, or fixed 8000 chars when context is unknown.
  hermes      : measured directly from ~/.hermes/.skills_prompt_snapshot.json
                (the real injected text) when present.
  openclaw    : skills.limits.maxSkillsPromptChars if set; cost via the documented
                formula 195 + Sum(97 + len(name)+len(description)+len(location)).

Usage: python3 check_listing_budget.py [project_root] [--platform NAME]
Exit:  0 = fits / measured ok
       1 = OVERFLOW (a finding — use the numbers, not an error)
       2 = budget unavailable (no platform, or context unknown -> ask the user)
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import detect_platform as dp  # noqa: E402

HOME = Path.home()
CHARS_PER_TOKEN = 4
PER_DESC_CAP_PORTABLE = 1024      # agentskills.io spec
PER_DESC_CAP_CC = 1536           # Claude Code >= 2.1.105
BAND = 300                       # everyday per-description target
BAND_CROWDED = 200               # target when 40+ skills installed
# OpenClaw documented listing cost (chars). docs.openclaw.ai/tools/skills
OPENCLAW_BASE = 195
OPENCLAW_PER_SKILL = 97

DESC_RE = re.compile(r"^description:\s*(.*?)(?=^[A-Za-z_-]+:|^---\s*$)", re.S | re.M)


def _front_matter(md_file: Path):
    """The YAML frontmatter block of a markdown file (one read), or None."""
    try:
        text = md_file.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    return m.group(1) if m else None


def _desc_from(block: str):
    d = DESC_RE.search(block + "\n---")
    if not d:
        return None
    val = d.group(1).strip()
    if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
        val = val[1:-1]
    return re.sub(r"\s+", " ", val).strip()  # platforms inject one space-joined line


def read_desc(md_file: Path):
    """description only (for slash commands, which key by filename)."""
    block = _front_matter(md_file)
    return _desc_from(block) if block is not None else None


def read_skill(md_file: Path):
    """(name, description) from a single read; (None, None) if no description."""
    block = _front_matter(md_file)
    if block is None:
        return None, None
    desc = _desc_from(block)
    if desc is None:
        return None, None
    nm = re.search(r"^name:\s*(.+)$", block, re.M)
    name = nm.group(1).strip().strip("\"'") if nm else md_file.parent.name
    return name, desc


def iter_skills(roots):
    """Yield (name, desc, path) for every SKILL.md under roots (rglob: nested
    layouts Codex/OpenClaw allow)."""
    for root in roots:
        rp = Path(root)
        if not rp.is_dir():
            continue
        for f in sorted(rp.rglob("SKILL.md")):
            name, desc = read_skill(f)
            if desc is not None:
                yield name, desc, f


def collect_from_roots(roots) -> dict:
    """name -> description, first seen wins."""
    out = {}
    for name, desc, _ in iter_skills(roots):
        out.setdefault(name, desc)
    return out


def collect_commands(cmd_dir: Path) -> dict:
    out = {}
    if not cmd_dir.is_dir():
        return out
    for f in cmd_dir.rglob("*.md"):
        desc = read_desc(f)
        if desc:
            out[f.stem] = desc
    return out


def fraction_budget(frac, ctx):
    """(budget_chars, basis) for fraction-of-context platforms."""
    return (int(frac * ctx * CHARS_PER_TOKEN),
            f"{frac:.0%} x {ctx//1000}k ctx x ~{CHARS_PER_TOKEN} chars/token")


def verdict(total, budget, overflow_suffix=""):
    return f"OVERFLOW x{total/budget:.1f}{overflow_suffix}" if total > budget else "fits"


def print_bands(skills: dict, n_skills: int):
    band = BAND_CROWDED if n_skills >= 40 else BAND
    over_band = [(len(d), n) for n, d in skills.items() if len(d) > band]
    over_cap = [(len(d), n) for n, d in skills.items() if len(d) > PER_DESC_CAP_PORTABLE]
    print(f"\nover {band}-char band ({len(over_band)} entries, top 15):")
    for length, name in sorted(over_band, reverse=True)[:15]:
        print(f"  {length:5d}  {name}")
    if over_cap:
        print(f"over per-description cap {PER_DESC_CAP_PORTABLE} (portable) / {PER_DESC_CAP_CC} (CC):")
        for length, name in sorted(over_cap, reverse=True):
            print(f"  {length:5d}  {name}")


def cc_budget(p, project_root):
    """Claude-Code-style fraction budget. Returns (budget, basis) or (None, reason)
    when the context window can't be resolved. SLASH_COMMAND_TOOL_CHAR_BUDGET is a
    Claude-Code-only override, so it lives in the CC path."""
    env = os.environ.get("SLASH_COMMAND_TOOL_CHAR_BUDGET")
    if env and env.isdigit():
        return int(env), "SLASH_COMMAND_TOOL_CHAR_BUDGET env"
    frac = p.get("fraction", 0.01)
    if project_root:
        try:
            v = json.loads((project_root / ".claude" / "settings.json").read_text("utf-8")).get("skillListingBudgetFraction")
            if isinstance(v, (int, float)) and v > 0:
                frac = float(v)
        except (OSError, ValueError):
            pass
    ctx = p.get("context_tokens")
    if not ctx:
        return None, "context window unknown — ask the user (200k? 1M?) and set it"
    return fraction_budget(frac, ctx)


def report_claude_code(p, project_root):
    glob_skills = collect_from_roots(p["skills_roots"])
    proj_skills = collect_from_roots([str(project_root / ".claude" / "skills")]) if project_root else {}
    plug = collect_from_roots([str(HOME / ".claude" / "plugins" / "cache")])
    shadowed = set(glob_skills) & set(proj_skills)
    for n in shadowed:
        glob_skills.pop(n, None)
    cmds = {**collect_commands(HOME / ".claude" / "commands"),
            **(collect_commands(project_root / ".claude" / "commands") if project_root else {})}
    every = {**glob_skills, **proj_skills, **plug, **cmds}
    if not every:
        print("no SKILL.md / command descriptions found")
        return 2
    total = sum(len(d) for d in every.values())
    budget, basis = cc_budget(p, project_root)
    print("== skill listing budget (claude_code) ==")
    print(f"sources: global={len(glob_skills)} project={len(proj_skills)} "
          f"plugin={len(plug)} commands={len(cmds)}"
          + (f"  (shadowed dupes dropped: {len(shadowed)})" if shadowed else ""))
    if budget is None:
        print(f"descriptions total: {total:,} chars   budget: UNAVAILABLE — {basis}")
        return 2
    print(f"descriptions total: {total:,} chars   budget ~= {budget:,} chars ({basis})")
    print(f"verdict: {verdict(total, budget, ' — expect silent name-only truncation')}")
    print("note: CC drop order is undocumented (#31505) — fit with margin")
    print_bands(every, len(glob_skills) + len(proj_skills) + len(plug))
    return 1 if total > budget else 0


def report_codex(p, project_root):
    skills = collect_from_roots(p["skills_roots"])
    if not skills:
        print("no SKILL.md descriptions found under Codex skill roots")
        return 2
    total = sum(len(d) for d in skills.values())
    ctx = p.get("context_tokens")
    if ctx:
        budget, basis = fraction_budget(p["fraction"], ctx)
    else:
        budget, basis = p["fixed_chars"], f"fixed {p['fixed_chars']} chars (context window unknown)"
    print("== skill listing budget (codex) ==")
    print(f"skills: {len(skills)}   descriptions total: {total:,} chars   budget ~= {budget:,} chars ({basis})")
    print(f"verdict: {verdict(total, budget, ' — Codex shortens descriptions, then omits skills with a warning')}")
    print_bands(skills, len(skills))
    return 1 if total > budget else 0


def report_hermes(p, project_root):
    snap = p.get("snapshot")
    skills = collect_from_roots(p["skills_roots"])
    print("== skill listing budget (hermes) ==")
    if snap and Path(snap).is_file():
        raw = Path(snap).read_text("utf-8", errors="replace")
        try:
            s = json.loads(raw).get("skills", {})
            n = len(s) if isinstance(s, (list, dict)) else len(skills)
        except ValueError:
            n = len(skills)
        injected = len(raw)
        ctx = p.get("context_tokens")
        frac = f" (~{100*injected/(ctx*CHARS_PER_TOKEN):.1f}% of {ctx//1000}k ctx)" if ctx else ""
        print(f"measured from snapshot: {injected:,} chars actually injected, {n} skills{frac}")
        print("note: Hermes publishes no listing cap; this is the real injected size, not an estimate")
    else:
        total = sum(len(d) for d in skills.values())
        print(f"skills: {len(skills)}   descriptions total: {total:,} chars")
        print("note: no .skills_prompt_snapshot.json and no public cap — size reported, no verdict")
    print_bands(skills, len(skills))
    return 0


def report_openclaw(p, project_root):
    records = list(iter_skills(p["skills_roots"]))
    if not records:
        print("no SKILL.md found under OpenClaw skill roots")
        return 2
    # documented cost: 195 + Sum(97 + len(name)+len(description)+len(location))
    bands = {name: desc for name, desc, _ in records}
    cost = OPENCLAW_BASE + sum(
        OPENCLAW_PER_SKILL + len(name) + len(desc) + len(str(path))
        for name, desc, path in records)
    cap = p.get("max_chars")
    print("== skill listing budget (openclaw) ==")
    print(f"skills: {len(records)}   injected cost ~= {cost:,} chars "
          f"({OPENCLAW_BASE} + Sum {OPENCLAW_PER_SKILL} + name + description + location)")
    if cap:
        print(f"cap (maxSkillsPromptChars): {cap:,} chars   verdict: {verdict(cost, cap)}")
        ret = 1 if cost > cap else 0
    else:
        print("note: skills.limits.maxSkillsPromptChars not set — cost reported, no cap to compare")
        ret = 0
    print_bands(bands, len(records))
    return ret


DISPATCH = {
    "claude_code": report_claude_code,
    "codex": report_codex,
    "hermes": report_hermes,
    "openclaw": report_openclaw,
}


def main() -> int:
    ap = argparse.ArgumentParser(description="Skill-listing budget vs platform")
    ap.add_argument("project_root", nargs="?", default=None)
    ap.add_argument("--platform", default=None)
    args = ap.parse_args()
    project_root = Path(args.project_root).resolve() if args.project_root else Path.cwd()

    found = dp.detect()
    if not found:
        print("no agent platform detected (Claude Code / Codex / Hermes / OpenClaw). "
              "Ask the user which platform + context window, then set them manually.")
        return 2

    if args.platform:
        sel = [p for p in found if p["platform"] == args.platform]
        if not sel:
            print(f"--platform {args.platform} not detected. Installed: {[p['platform'] for p in found]}")
            return 2
        target = sel[0]
    else:
        target = found[0]
        if len(found) > 1:
            print(f"NOTE: multiple platforms installed {[p['platform'] for p in found]}; "
                  f"reporting '{target['platform']}'. Pass --platform to override.\n")

    return DISPATCH[target["platform"]](target, project_root)


if __name__ == "__main__":
    sys.exit(main())
