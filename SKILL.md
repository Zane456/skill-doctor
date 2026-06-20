---
name: skill-doctor
description: Skill quality + package structure expert. ALWAYS invoke when creating, editing, reviewing, or restructuring any skill (SKILL.md, references/, scripts/, routing, indexes), or on 审查/体检/修复/重构/拆分 skill. Do not modify or split a skill directly — use this skill first.
---

# Skill Doctor

Diagnose and improve any SKILL.md. **A compass, not a manual** — the concrete standards live in `references/`, read on demand.

## Diagnosis flow after triggering (each step must produce visible output)

> A step with no visible output gets silently skipped (Seleznov experiment, 2026). Print one confirmation line per step.
> **Self-review flag**: if this session has already Edited/Written the target SKILL.md, **prefix every doctor print line with `[self-review]`**, and append one line at the end of Step 3: "conclusion is self-assessed, recommend re-reviewing with a fresh sub-agent." Credibility is discounted, visibility is forced.

### Step 1: Read the target SKILL.md, announce the diagnosis start

Read the full text of the SKILL.md being edited, run `python3 <this-skill-dir>/scripts/check_listing_budget.py "<project_root>"` (quote the path — spaces are common), print two lines:
```
[skill-doctor] Auditing: <path>  body=<N> lines  description=<M> chars
[skill-doctor] Budget (<platform>): <K> skills, <T> chars vs ≈<B> → <fits | OVERFLOW ×N.N>
```
Auto-detects platform (CC / Codex / Hermes / OpenClaw). Exit: 0 = fits; 1 = overflow; 2 = unavailable (no platform / context unknown → ask the user's platform + window). **Overflow is a population-level NOTICE, not a finding against the audited skill**: print the numbers so the user knows, but do NOT shorten this skill's description for budget reasons — slimming is a global pass, never a single-skill fix.

### Step 2: Judge against the dimensions

Pick the dimensions to load from the [reference index](references/index.md) (**Dimensions** section) — read **only** the entries whose *when-to-read* fires.
After loading, print one line:
```
[skill-doctor] Loaded: <list>;  Skipped: <list with one-word reason>
```

### Step 2.5: Dry-run walkthrough (only when body contains a workflow)

Following `references/effect-dry-run.md`, take the 1 most typical prompt and walk it through the body steps, checking whether input/instruction/output connect.
Any broken link or ambiguity → mark **P0** (effect problem) and put it in the Code layer (P0 bucket) of Step 3.
Print one line:
```
[skill-doctor] Dry-run prompt: "<prompt>"  broken links=<N>
```
If the body has no workflow (pure rule / reference-type skill), print:
```
[skill-doctor] Dry-run: skipped (no workflow)
```

### Step 2.6: Live-injection check (only when the target skill is in the current session's scope)

Check whether the target appears in this session's available-skills list **with its description** (not name-only). The 3 cases (injected / name-only budget-drop / out-of-scope skip) and the population-notice rule are in `references/live-injection-check.md`. Print one line:
```
[skill-doctor] Live-injection: <injected | DROPPED (name-only) | skipped (<reason>)>
```

### Step 3: Output the diagnosis report

Present per `references/output-format.md` — a **layered report in lesstoken style, in the user's reply language**: verdict → quality scores → **Code layer** (P0→P3 findings with file:line/field — the evidence) → **Decision layer** split **✅ Safe to fix now** vs **🤔 Needs your decision** → closing question. Actionable parts last.

Substance that fills the layers:
- Each finding: stable ID (`P0-1` …), a **specific line number or field** (no vagueness), risk circle 🟢/🟡/🔴, sorted P0→P3 (`references/priority-tiers.md`). Same violation in N places → **N separate findings**, never merge.
- **Name the failure mode** when one applies (`references/predictability-glossary.md`): prefix `[no-op]`/`[sediment]`/`[premature-completion]`/`[weak-leading-word]`/`[duplication]`/`[sprawl]`. Prefix = what kind, P-tier = how bad; never replaces the tier.
- Each 🤔 item separates **mechanism** (how the skill behaves now) from **consequence** (what the next LLM does wrong at run time), then options + rec.

### Step 4: Apply with Edit after user confirmation

**Never** Edit without confirmation. Wait for the user to say "fix it" before acting.

Before acting, apply the **size gate** and the **pre-deletion check**; afterwards **close the loop** — full procedure in `references/apply-safety.md`.
After fixing, print one line:
```
[skill-doctor] Applied <N> fixes to <path>  body: <old>→<new> lines (<+X%>)
```

## Hard rules quick reference

The quantified hard rules (a violation is an error, not a suggestion) live in `references/hard-rules.md` — consult on every audit.

## Exception fallback

When a path is missing, YAML won't parse, or a bundled script (`scripts/check_listing_budget.py` + `scripts/detect_platform.py` / `scripts/check_routes.py` / `scripts/eval_retrieval.py` / `scripts/check_desc_slim.py`) is missing or exits 2 — handle per `references/exception-fallback.md`. Announce the exception to the user first; never silently skip.

## Output & language

Report prose follows `references/output-style.md` (clear, terminal-safe, conclusion-first). Body/references default to English; flag unjustified non-English ⚠️ — policy + the two justified exceptions in `references/language-policy.md`.

## Out of scope for this skill

- Whether the actual **functionality** is correct (that is a logic bug, not a skill-form problem)
- Project-specific conventions (those go in CLAUDE.md, not a skill)
- One-off fix scripts (discarded after running once, should not be a skill)

## Why this skill exists

Why LLMs mis-write SKILL.md as a manual, and how this skill splits mechanical checks from judgment: `references/rationale.md`.
