#!/usr/bin/env python3
"""detect_platform.py — which agent platform(s) are installed, and how each one
budgets its skill listing.

NON-INTERACTIVE. Prints findings (text or --json) and exits. It never prompts —
any choice (which platform to install into, whether to enable the LLM check) is
left to the caller (a human in a chat box, or the GETTING_STARTED flow the agent
runs on their behalf).

Why detect by CONFIG FILE, not by skills dir: `~/.agents/skills` is shared by
both Codex (USER scope) and OpenClaw (personal scope), so a skills dir alone is
ambiguous. The config file disambiguates:
  Claude Code -> ~/.claude            (settings.json)
  Codex       -> ~/.codex/config.toml
  Hermes      -> ~/.hermes/config.yaml
  OpenClaw    -> ~/.openclaw/openclaw.json

Each platform injects every skill's name+description into the system prompt under
a budget and degrades on overflow; only the constants and the read differ:
  Claude Code : ~1% of the model context window; silent name-only truncation.
  Codex       : ~2% of the model context window, or 8000 chars if unknown;
                shortens descriptions first, then omits skills WITH a warning.
  Hermes      : has ~/.hermes/.skills_prompt_snapshot.json — the actual injected
                text; measure it directly instead of estimating.
  OpenClaw    : skills.limits.maxSkillsPromptChars in openclaw.json; deterministic
                cost = 195 + Σ(97 + len(name)+len(description)+len(location)).
"""
import json
import os
import re
import sys
from pathlib import Path

HOME = Path.home()

# Context window per model family (chars budget = fraction x tokens x ~4 chars/token).
# A "[1m]" suffix opts into the 1M variant. Unknown model -> None (caller asks user).
MODEL_CONTEXT_TOKENS = {
    "glm-5.2": 200_000, "glm-5.1": 200_000,
    "gpt-5": 400_000, "gpt-5.5": 400_000, "gpt-5.4": 400_000, "gpt-5-pro": 400_000,
    "claude-opus-4-8": 200_000, "claude-sonnet-4-6": 200_000, "claude-haiku-4-5": 200_000,
    "gemini-2.5-pro": 1_000_000, "gemini-3.5-pro": 1_000_000,
}


def context_tokens_for(model: str):
    """Best-effort context window (tokens) for a model id, or None if unknown."""
    if not model:
        return None
    m = model.strip().lower()
    if "[1m]" in m:
        return 1_000_000
    base = m.split("[")[0]
    if base in MODEL_CONTEXT_TOKENS:
        return MODEL_CONTEXT_TOKENS[base]
    for key, val in MODEL_CONTEXT_TOKENS.items():  # prefix match (e.g. provider/model)
        if key in base:
            return val
    return None


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _loads_lenient(text: str):
    """json.loads, tolerant of JSON5-isms OpenClaw uses (// and /* */ comments,
    trailing commas). Best-effort: returns {} on failure."""
    if not text.strip():
        return {}
    no_block = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    no_line = re.sub(r"(^|\s)//[^\n]*", r"\1", no_block)
    no_trailing = re.sub(r",(\s*[}\]])", r"\1", no_line)
    for candidate in (text, no_trailing):
        try:
            return json.loads(candidate)
        except ValueError:
            continue
    return {}


def _codex_model() -> str:
    txt = _read(HOME / ".codex" / "config.toml")
    m = re.search(r'^\s*model\s*=\s*"([^"]+)"', txt, re.M)
    return m.group(1) if m else ""


def _hermes_model() -> str:
    txt = _read(HOME / ".hermes" / "config.yaml")
    # model:\n  default: <id>
    m = re.search(r"^model:\s*\n(?:\s+.*\n)*?\s+default:\s*(\S+)", txt, re.M)
    return m.group(1).strip().strip('"\'') if m else ""


def _claude_context_tokens(d) -> "int | None":
    env = d.get("env", {})
    v = env.get("CLAUDE_CODE_MAX_CONTEXT_TOKENS") or d.get("CLAUDE_CODE_MAX_CONTEXT_TOKENS")
    return int(v) if v and str(v).isdigit() else None


def _claude_fraction(d) -> float:
    v = d.get("skillListingBudgetFraction")
    return float(v) if isinstance(v, (int, float)) and v > 0 else 0.01


def _openclaw_max_chars():
    cfg = HOME / ".openclaw" / "openclaw.json"  # JSON5: comments / trailing commas
    d = _loads_lenient(_read(cfg))
    return (d.get("skills", {}).get("limits", {}) or {}).get("maxSkillsPromptChars")


def detect():
    """Return a list of installed-platform dicts. Order = detection priority."""
    out = []

    # Claude Code
    if (HOME / ".claude").is_dir():
        cs = _loads_lenient(_read(HOME / ".claude" / "settings.json"))
        out.append({
            "platform": "claude_code",
            "config": str(HOME / ".claude" / "settings.json"),
            "skills_roots": [str(HOME / ".claude" / "skills")],
            "install_target": str(HOME / ".claude" / "skills"),
            "model": "",
            "context_tokens": _claude_context_tokens(cs),
            "budget_rule": "fraction",
            "fraction": _claude_fraction(cs),
            "truncation": "silent name-only",
        })

    # Codex (config file disambiguates from OpenClaw on shared ~/.agents/skills)
    if (HOME / ".codex" / "config.toml").is_file():
        model = _codex_model()
        roots = [str(HOME / ".codex" / "skills"), str(HOME / ".agents" / "skills")]
        out.append({
            "platform": "codex",
            "config": str(HOME / ".codex" / "config.toml"),
            "skills_roots": [r for r in roots if Path(r).is_dir()] or roots[:1],
            "install_target": str(HOME / ".agents" / "skills"),
            "model": model,
            "context_tokens": context_tokens_for(model),
            "budget_rule": "fraction_or_fixed",
            "fraction": 0.02,
            "fixed_chars": 8000,
            "truncation": "shorten then omit, with warning",
        })

    # Hermes
    if (HOME / ".hermes" / "config.yaml").is_file():
        model = _hermes_model()
        snap = HOME / ".hermes" / ".skills_prompt_snapshot.json"
        out.append({
            "platform": "hermes",
            "config": str(HOME / ".hermes" / "config.yaml"),
            "skills_roots": [str(HOME / ".hermes" / "skills")],
            "install_target": str(HOME / ".hermes" / "skills"),
            "model": model,
            "context_tokens": context_tokens_for(model),
            "budget_rule": "snapshot",
            "snapshot": str(snap) if snap.is_file() else "",
            "truncation": "unknown",
        })

    # OpenClaw
    if (HOME / ".openclaw" / "openclaw.json").is_file() or (HOME / ".openclaw").is_dir():
        roots = [str(HOME / ".openclaw" / "skills"), str(HOME / ".agents" / "skills")]
        out.append({
            "platform": "openclaw",
            "config": str(HOME / ".openclaw" / "openclaw.json"),
            "skills_roots": [r for r in roots if Path(r).is_dir()] or roots[:1],
            "install_target": str(HOME / ".openclaw" / "skills"),
            "model": "",
            "context_tokens": None,
            "budget_rule": "max_chars_or_formula",
            "max_chars": _openclaw_max_chars(),
            "truncation": "config-gated + per-skill char budget",
        })

    return out


def main():
    as_json = "--json" in sys.argv
    found = detect()
    if as_json:
        print(json.dumps(found, indent=2))
        return
    if not found:
        print("[detect_platform] no known agent platform detected "
              "(Claude Code / Codex / Hermes / OpenClaw). Ask the user which one they use.")
        return
    print(f"[detect_platform] detected {len(found)} platform(s):")
    for p in found:
        ctx = p.get("context_tokens")
        ctx_s = f"{ctx//1000}k" if ctx else "unknown (ask user)"
        print(f"  - {p['platform']}: model={p['model'] or 'n/a'}  context={ctx_s}  "
              f"install_target={p['install_target']}")


if __name__ == "__main__":
    main()
