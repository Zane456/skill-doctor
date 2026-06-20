# Description Templates and Trigger Strength

The description is the **only mechanism** for triggering — the body's content is loaded only after triggering. If the description is written badly, no matter how good the body is, it does not matter.

## Empirical comparison of three schools of templates

The community has done empirical testing (Seleznov, 650-trial experiment, 2026):

| School | Template | Measured trigger rate |
|--------|----------|----------------------|
| Anthropic official | "[What it does]. Use when [when]." | ~50% |
| Superpowers | "Use when [when]" (no workflow summary) | not tested separately, roughly the same |
| **Seleznov experimental** | **"[Domain] expert. ALWAYS invoke this skill when [trigger]. Do not [alternative] directly. Use this skill first."** | **~100%** |

> Data source: [Marc Bara — Claude Skills Have Two Reliability Problems](https://medium.com/@marc.bara.iniesta/claude-skills-have-two-reliability-problems-not-one-299401842ca8)

## Recommended: the Seleznov three-part template

```yaml
description: <Domain> expert. ALWAYS invoke this skill when <trigger conditions>.
  Do not <competing default action> directly. Use this skill first.
```

None of the three components can be omitted:

1. **Domain identifier** — lets Claude know what domain of expert this is
   - ✅ "SKILL.md quality expert"
   - ✅ "PostgreSQL performance optimizer"
   - ❌ "Helper for skills" (too weak)

2. **Directive keyword** — use "ALWAYS invoke this skill when...", **not** "Use when..."
   - "Use when" is a suggestive tone, Claude weighs it against its own priorities
   - "ALWAYS invoke" is a command, the trigger rate jumps from 50% to 100%

3. **Negative constraint** — blocks Claude's "detour default behavior"
   - e.g. "Do not modify SKILL.md directly without consulting this skill first."
   - e.g. "Do not write SQL queries directly—use this skill first."
   - This is the **most counterintuitive but most critical** item in the Seleznov experiment. Without it, the trigger rate collapses.

## The first 50 characters are prime real estate

Claude weights the front of the description heavily when scanning. **The most important keywords / trigger scenarios must be within the first 50 characters.**

```yaml
# ❌ keywords buried too deep
description: This skill provides comprehensive guidance and tooling support for
  the workflow of editing SKILL.md files...

# ✅ keywords up front
description: SKILL.md quality expert. ALWAYS invoke when editing any SKILL.md...
```

## The character budget: a shared, silent ceiling

Two independent limits (Claude Code; sources: issues #56710, #47627, v2.1.105 release notes):

- **Per description**: 1024 chars (portable agentskills.io spec); Claude Code ≥ 2.1.105 accepts up to 1536.
- **Whole listing, all sources combined** (global + project + plugin skills, plus slash commands): budget = **`skillListingBudgetFraction` (default 1%) × the CURRENT MODEL's context window**, converted to chars (≈ ×4). It is **dynamic, not a fixed char ceiling** — it scales with whatever model you are actually running (official docs: "the budget scales at 1% of the model's context window"). Rough sizes: a 200k-context model ≈ 8k chars at 1% / 16k at 2%; a **1M-context model ≈ 40k at 1% / 80k at 2%**. The old "≈8–16k absolute" figure is the 200k-era value baked into early versions (the fraction setting shipped in v2.1.129) — do not treat it as a frozen cap. On overflow Claude Code **drops entire descriptions and keeps names only** — no error, no warning; a name-only skill cannot auto-trigger. ⚠️ The budget tracks the *live* model, so a 200k-context sub-agent shrinks it back to the 8–16k band even if the main session is on 1M.
- Which skills keep their descriptions is **undocumented and not user-controllable** (#31505). Do not bet on priority — fit the budget with margin.

Measure before judging: `scripts/check_listing_budget.py [project_root]` sums every installed description and compares against the estimated budget.

Levers, in order of preference:
1. **Shorten descriptions** (free, robust — see the reconciliation rule below).
2. **Uninstall or merge** skills that rarely trigger.
3. **Raise the budget**: `{"skillListingBudgetFraction": 0.02}` in settings.json (v2.1.129+; costs ~11k extra tokens every session) or `SLASH_COMMAND_TOOL_CHAR_BUDGET=<chars>` env var.

Target bands: **≤ 300 chars** as the everyday default; **≤ 200 chars when ~40+ skills are installed**.

## When keyword coverage conflicts with the budget — budget wins

**Scope: this compression rule applies only to a user-initiated GLOBAL slimming pass, or when writing a brand-new description.** During a single-skill audit, budget overflow is notify-only — never shorten the audited skill's existing description on your own initiative (length is a population matter, not a single-skill defect).

The Seleznov template plus wide keyword coverage inflates descriptions toward 600–1000 chars. Over budget this self-defeats: a dropped description triggers at 0%, template or not. Compress in this order; the last item is untouchable:

1. Cut workflow hints, justifications, scope essays ("Out of scope: …" prose) — that is the body's job.
2. Cut synonym families down to the 2–3 forms the user actually types; keep bilingual triggers only for words the user really uses in both languages.
3. Shorten the negative constraint to one short clause.
4. Never cut: first-50-chars domain + core trigger keywords, "ALWAYS invoke", one negative constraint.

Compact Seleznov form (~150–250 chars, trigger power preserved):

```yaml
description: <Domain> expert. ALWAYS invoke when <2–3 concrete triggers, incl. the user's own words>. Do not <competing default> directly.
```

## Slimming safety protocol (mandatory during a global pass — machine-gated, no per-skill user confirmation)

The silent failure mode of slimming is identical to budget truncation: a cut trigger
word the user actually types → that phrasing never triggers again, no error. The user
is NOT asked to confirm each cut; safety comes from restricting what slimming is
allowed to be, then verifying it deterministically:

1. **Deletion-only, whole sentences.** Slimming = removing complete sentences of the
   safe class (provenance "Cloned from…", scope essays "Out of scope: …", workflow
   summaries, justification prose). Kept text stays verbatim — no rewriting, no
   paraphrasing, no merging. Trigger material (Triggers: lists, quoted phrasings,
   backticked tokens, "ALWAYS invoke", the negative constraint) is never touched.
2. **Deterministic gate, every skill.** Back up first (`cp SKILL.md SKILL.md.bak`),
   edit, then run `python3 <this-skill-dir>/scripts/check_desc_slim.py SKILL.md.bak SKILL.md`.
   Exit 1 (a kept sentence was rewritten, or a protected trigger span vanished) →
   restore the backup, do not negotiate with the gate. Exit 0 → keep; the removed
   sentences print as a log for later review, no approval needed.
3. **If the target band is unreachable by sentence-deletion alone, STOP** and report
   that skill to the user instead of escalating to rewrites — rewriting trigger
   sentences is exactly the risk this protocol exists to exclude.
4. **Post-batch verification.** Restart the session, re-run
   `scripts/check_listing_budget.py`, and confirm Step 2.6 shows descriptions injected.
5. **Ground-truth trigger regression (optional, costs real Claude runs).** For skills
   whose triggering matters most, use skill-creator's `scripts/run_eval.py` — it spawns
   real `claude -p "<query>"` subprocesses against the slimmed description and measures
   the actual trigger rate (queries live in an explicit evals.json the user can edit).
   That is the end-to-end test this protocol's static checks approximate; quote the run
   count before launching.

## Third person is a hard rule

The description is injected into the system prompt. First/second person breaks discovery:

```yaml
# ❌ first person
description: I help you write better SKILL.md files...
# ❌ second person
description: You can use this to review SKILL.md...
# ✅ third person
description: SKILL.md quality expert. ALWAYS invoke when...
```

## Keyword coverage

The description should pack in the words the user **actually says**, including synonyms and both languages:

- Mixed languages (if the user switches between them): "SKILL.md quality expert. ALWAYS invoke when editing/modifying/reviewing any SKILL.md, or when the user asks to audit/fix/improve a skill."
- Synonym family: "edit / write / modify / fix / review / audit / improve / check"
- Error messages (if the skill handles a specific error): "ENOENT", "permission denied"
- Specific tool names / file names / commands

## Anti-example collection

```yaml
# ❌ too vague
description: Helps with skills

# ❌ summarizes the workflow (Claude reads the description, takes a shortcut, never enters the body)
description: SKILL.md reviewer that reads the file, scans frontmatter, checks
  body length, validates references, and suggests fixes for each issue found.

# ❌ no negative constraint
description: SKILL.md expert. ALWAYS invoke when editing SKILL.md.
# the trigger rate drops back from 100% to 50% — Claude thinks it can edit too

# ✅ standard form
description: SKILL.md quality expert. ALWAYS invoke this skill when editing
  or writing any SKILL.md file. Do not modify SKILL.md directly without
  consulting this skill first. Use this skill first.
```

## Empty-phrasing check (a standalone hard fault)

Any of the following "filler words" in a description dilutes keyword weight — especially fatal in the first 50 characters:

| Empty word | Why it is bad |
|------------|---------------|
| various / many / multiple / several | conveys no domain information |
| useful / helpful / handy | every skill claims to be useful, no distinction |
| general / generic / all-purpose | negates specialization (the antonym of an expert description) |
| things / tasks / stuff / items | no concrete noun, no trigger scenario to extract |
| comprehensive / robust / powerful | marketing speak, zero contribution to the discovery mechanism |

Anti-example:
```yaml
# ❌ all 5 empty words present
description: A comprehensive skill for various useful tasks including many helpful operations.

# ✅ replaced with a concrete domain + trigger verbs
description: PostgreSQL query optimizer. ALWAYS invoke when writing or reviewing SQL...
```

## Diagnostic checklist (skill-doctor checks against this when reading this reference)

- [ ] Do the first 50 characters contain the core trigger keywords?
- [ ] Does it use "ALWAYS invoke" (not "Use when")?
- [ ] Is there a negative constraint ("Do not X directly")?
- [ ] Is it third person?
- [ ] Within the per-description cap (1024 portable / 1536 CC)? (the ≤300/≤200 band is guidance for NEW or user-requested rewrites — never a standalone must-fix on an existing skill)
- [ ] Population fits the shared listing budget? (`scripts/check_listing_budget.py` — **notify-only**, report the verdict and move on)
- [ ] Live-injection: does the **current session's** available-skills list show this skill's description (not name-only)?
- [ ] Does it cover the synonyms / both languages the user actually says (trimmed per the budget reconciliation rule)?
- [ ] Does it **not** summarize the workflow (it should only say "when to use" + "what expert it is")?
- [ ] Does it have **no** empty phrasing (various / many / useful / general / things / comprehensive, etc.)?
