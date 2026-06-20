#!/usr/bin/env python3
"""check_listing_budget.py — sum installed skill descriptions vs Claude Code's listing budget.

The skills list injected into the system prompt shares one budget (≈1% of the
context window; CC issues #56710 / #47627). On overflow CC silently drops entire
descriptions and keeps names only — a name-only skill cannot auto-trigger.
This script measures the population so skill-doctor can judge one skill in context.

Usage: python3 check_listing_budget.py [project_root]
Exit:  0 = fits budget
       1 = OVERFLOW (this is a finding — use the printed numbers, do not treat as error)
       2 = nothing found / script error (only this exit means "budget unavailable")

Budget estimate (chars) =
  SLASH_COMMAND_TOOL_CHAR_BUDGET env var, if set (CC treats it as chars), else
  skillListingBudgetFraction (project settings.json > ~/.claude/settings.json,
  default 0.01) x CONTEXT_TOKENS x CHARS_PER_TOKEN.
Estimate only: CC's exact drop order is undocumented (#31505) — fit with margin.
Counted pools: global skills, project skills (project shadows global on same
name, only one copy counted), plugin skills, and slash commands (~/.claude/commands
+ <project>/.claude/commands) which share the same listing pool.
"""
import json
import os
import re
import sys
from pathlib import Path

HOME = Path.home()
CONTEXT_TOKENS = int(os.environ.get("SKILL_DOCTOR_CONTEXT_TOKENS", 1_000_000))
# CC's budget scales with the CURRENT model's context window (official docs:
# "the budget scales at 1% of the model's context window"), NOT a fixed ceiling.
# Default assumes the user's main model is 1M-context (Opus 4.8 [1m]). Override
# with SKILL_DOCTOR_CONTEXT_TOKENS=200000 when auditing for a 200k model/sub-agent.
CHARS_PER_TOKEN = 4               # rough chars/token for budget conversion
DEFAULT_FRACTION = 0.01
PER_DESC_CAP_PORTABLE = 1024      # agentskills.io spec
PER_DESC_CAP_CC = 1536            # Claude Code >= 2.1.105
BAND = 300                        # everyday per-description target
BAND_CROWDED = 200                # target when 40+ skills installed

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
    # CC injects a space-joined single line; collapse whitespace before counting
    return re.sub(r"\s+", " ", val).strip()


def collect_skills(root: Path, patterns: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for pat in patterns:
        try:
            for f in root.glob(pat):
                desc = read_desc(f)
                if desc is not None:
                    out[f.parent.name] = desc
        except OSError:
            continue
    return out


def collect_commands(cmd_dir: Path) -> dict[str, str]:
    """Slash commands (*.md) share the listing pool; description frontmatter optional."""
    out: dict[str, str] = {}
    if not cmd_dir.is_dir():
        return out
    for f in cmd_dir.rglob("*.md"):
        desc = read_desc(f)
        if desc:
            out[f.stem] = desc
    return out


def load_fraction(project_root: Path | None) -> float:
    candidates = []
    if project_root:
        candidates.append(project_root / ".claude" / "settings.json")
    candidates.append(HOME / ".claude" / "settings.json")
    for p in candidates:
        try:
            v = json.loads(p.read_text(encoding="utf-8")).get("skillListingBudgetFraction")
            if isinstance(v, (int, float)) and v > 0:
                return float(v)
        except (OSError, ValueError):
            continue
    return DEFAULT_FRACTION


def main() -> int:
    # project_root is kept for settings lookup even when it has no .claude/skills
    project_root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()

    glob_skills = collect_skills(HOME / ".claude" / "skills", ["*/SKILL.md"])
    proj_skills = collect_skills(project_root / ".claude" / "skills", ["*/SKILL.md"])
    plugin_cache = HOME / ".claude" / "plugins" / "cache"
    plug_skills = collect_skills(plugin_cache,
                                 ["*/skills/*/SKILL.md", "*/*/skills/*/SKILL.md",
                                  "*/*/*/skills/*/SKILL.md", "*/*/*/*/skills/*/SKILL.md"])
    if plugin_cache.is_dir() and any(plugin_cache.iterdir()) and not plug_skills:
        print("WARNING: plugin cache is non-empty but 0 plugin SKILL.md matched - layout changed, plugin pool uncounted", file=sys.stderr)

    # project shadows global on the same skill name: count one copy only
    shadowed = set(glob_skills) & set(proj_skills)
    for name in shadowed:
        del glob_skills[name]

    cmds = {**collect_commands(HOME / ".claude" / "commands"),
            **collect_commands(project_root / ".claude" / "commands")}

    groups = {"global": glob_skills, "project": proj_skills,
              "plugin": plug_skills, "commands": cmds}
    every = [(name, src, desc) for src, g in groups.items() for name, desc in g.items()]
    if not every:
        print("no SKILL.md / command descriptions found in any source")
        return 2

    total = sum(len(d) for _, _, d in every)
    env = os.environ.get("SLASH_COMMAND_TOOL_CHAR_BUDGET")
    if env and env.isdigit():
        budget, basis = int(env), "SLASH_COMMAND_TOOL_CHAR_BUDGET env"
    else:
        frac = load_fraction(project_root)
        budget = int(frac * CONTEXT_TOKENS * CHARS_PER_TOKEN)
        basis = f"{frac:.0%} x {CONTEXT_TOKENS // 1000}k ctx x ~{CHARS_PER_TOKEN} chars/token"

    n_skills = len(every) - len(cmds)
    band = BAND_CROWDED if n_skills >= 40 else BAND
    print(f"== skill listing budget ==")
    print(f"sources: " + "  ".join(f"{k}={len(v)}" for k, v in groups.items())
          + (f"   (shadowed dupes dropped: {len(shadowed)})" if shadowed else ""))
    print(f"descriptions total: {total:,} chars   budget ~= {budget:,} chars ({basis})")
    verdict = "fits" if total <= budget else f"OVERFLOW x{total / budget:.1f} - expect silent name-only truncation"
    print(f"verdict: {verdict}")
    print(f"note: drop order is undocumented (#31505) - fit with margin; context window assumed {CONTEXT_TOKENS // 1000}k")

    over_band = [(len(d), name, src) for name, src, d in every if len(d) > band]
    over_cap = [(len(d), name, src) for name, src, d in every if len(d) > PER_DESC_CAP_PORTABLE]
    print(f"\nover {band}-char band ({len(over_band)} entries, top 15):")
    for length, name, src in sorted(over_band, reverse=True)[:15]:
        print(f"  {length:5d}  {name}  ({src})")
    if over_cap:
        print(f"over per-description cap {PER_DESC_CAP_PORTABLE} (portable) / {PER_DESC_CAP_CC} (CC):")
        for length, name, src in sorted(over_cap, reverse=True):
            print(f"  {length:5d}  {name}  ({src})")
    return 0 if total <= budget else 1


if __name__ == "__main__":
    sys.exit(main())
