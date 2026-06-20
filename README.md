English | [简体中文](README.zh-CN.md)

<div align="center">

# skill-doctor

<p align="center">
  <img src="assets/hero.png" alt="skill-doctor — health check for AI agent skills: diagnose SKILL.md trigger reliability, routing recall, and package structure" width="760" />
</p>

> *"A skill the model never triggers is just dead documentation."*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Claude%20Code%20%2B%20Codex-blueviolet.svg)]()
[![Checks](https://img.shields.io/badge/checks-4%20deterministic-2ea44f.svg)]()
[![Type](https://img.shields.io/badge/type-meta--skill-blue.svg)]()

<br>

**Reviews your agent skills so the model actually triggers them, reads them whole, and routes through them cleanly.**

<br>

A broken skill never errors. It just doesn't fire, or the model reads half of it and moves on — and you find out weeks later that the skill you wrote never triggered once. skill-doctor is the pass that catches that. It scores how reliably a `SKILL.md` triggers, runs a routing-recall test on every reference file, names the failure mode, and restructures the package when the routing breaks. Four deterministic scripts carry the core checks; none needs an API key.

<br>

[See it in action](#see-it-in-action) · [Up and running](#up-and-running) · [What it catches](#what-it-catches) · [How it works](#how-it-works) · [Reference](#reference)

</div>

---

## See It in Action

Point it at a skill. It prints a diagnosis, not a grammar report:

```text
[skill-doctor] Auditing: my-skill/SKILL.md   body=142 lines   description=64 chars
[skill-doctor] Budget: 38 skills installed, 31k chars vs ≈40k → fits
[skill-doctor] Dry-run prompt: "use my-skill to tag the photo"   broken links=1

[skill-doctor] Diagnosis

❌ Must fix (P0→P3)
  [P0 effect break]   Step 3 reads a file Step 1 never writes → the workflow dead-ends
  [P1 trigger]        description has no negative constraint → ~50% trigger rate, not ~100%
  [P2 specificity]    "process the image" has no command → name one (e.g. `sips -s format png`)

⚠️ Suggested
  - [no-op] body opens with "This skill helps you…" — the model skips it → delete the line
  - [sprawl] references/tips.md mixes 3 unrelated topics → split by topic, one file each

✅ Passed
  - routing: 2 hops, 0 orphans, 0 dangling links
  - every workflow step prints visible output
```

It won't tell you a comma is missing. It tells you the model will silently skip Step 3, and that your description fires about half the time — then says exactly why.

---

## Up and Running

A skill installs by living in your skills folder:

```bash
git clone https://github.com/Zane456/skill-doctor.git ~/.claude/skills/skill-doctor
```

The four scripts run on Python 3 with zero dependencies. Routing, budget, and structure need nothing else. One optional check — the GLM routing-recall test — calls an LLM, so it reads a key from the environment:

```bash
export GLM_API_KEY=your_zai_key   # optional, only for the routing-recall test
```

Then, inside **Claude Code or Codex**, just ask — *"audit this SKILL.md"* / *"审查这个 skill"* — or invoke `skill-doctor` directly. It reads the target, runs the checks, walks one real prompt through the workflow, and prints a P0→P3 report. It does **not** edit your files until you say so.

---

## What It Catches

The failures that never announce themselves:

| Symptom you'd never notice | What it flags |
| :--- | :--- |
| The skill fires about half the time | description with no negative constraint, or "Use when" instead of "ALWAYS invoke" — ~50% vs ~100% trigger ([650-trial study](https://medium.com/@marc.bara.iniesta/claude-skills-have-two-reliability-problems-not-one-299401842ca8)) |
| It never auto-fires at all | description first-person, or the whole listing overflows the budget and drops to name-only |
| The model reads half and moves on | body past ~500 lines — `[sprawl]` |
| A reference file is never read | orphan or dangling route, caught by `check_routes.py` |
| A workflow step gets skipped | the step prints nothing, so the model walks past it |
| The agent quits a step early | exit condition too vague — `[premature-completion]` |
| A line that changes nothing | the model already obeyed it by default — `[no-op]` |

Every check, threshold, and rule is listed in full under [Reference](#reference).

---

## How It Works

Every step prints a line — a step with no visible output is a step the model silently skips.

```text
  SKILL.md + references/ + scripts/
        |
        v
  deterministic scripts ...... routes · budget · description-slim   (exit-coded, no LLM)
        |
        v
  GLM routing-recall ......... vote 3x per reference file           (optional, needs a key)
        |
        v
  judgment dimensions ........ trigger strength · failure modes     (loaded on demand)
        |
        v
  dry-run one real prompt .... does Step N get an input no earlier step produced?
        |
        v
  P0 -> P3 diagnosis ......... each finding tagged with its failure mode
        |
        v
  apply after you confirm .... then re-run check_routes to verify
```

Two choices make the verdict worth trusting:

- **Deterministic where it can be.** Counts, routing, and budget are settled by scripts that return exit codes — not an opinion that drifts between runs.
- **Honest where it can't.** If skill-doctor already edited your skill earlier in the same session, it stamps every line of its report `[self-review]` and tells you to re-check with a fresh agent. It discounts its own grade on purpose.

<!-- ============ Reference — skip unless you're looking something up ============ -->

---

## Reference

Lookup material. You don't need any of it to use the skill.

### Diagnosis flow

| Step | Does | Output |
| :--- | :--- | :--- |
| 1 | Read the target SKILL.md; count every installed description against the listing budget | body/description size + budget verdict |
| 2 | Load only the dimensions whose `when-to-read` fires | the loaded/skipped list |
| 2.5 | Dry-run: walk the single most typical prompt through the body | broken-link count (any → P0) |
| 2.6 | Live-injection: is the target's description actually injected this session, or dropped name-only | injected / dropped / skipped |
| 3 | Print the P0→P3 diagnosis (❌ must fix · ⚠️ suggested · ✅ passed), each finding tagged with a failure mode | the report |
| 4 | Apply fixes with Edit — only after you confirm — then re-run `check_routes.py` | applied-fixes line |

### Bundled scripts

No LLM and no third-party dependencies, except `eval_retrieval.py`, which calls a model on request.

| Script | Checks | Command | Exit |
| :--- | :--- | :--- | :--- |
| `check_routes.py` | reachability, orphans, dangling links, the 6000-char compass cap; `--before <snapshot>` adds a content-conservation check | `python3 scripts/check_routes.py <skill_dir>` | 0 clean / 1 issues |
| `check_listing_budget.py` | total description chars vs the ~1%-of-context listing pool; lists every description over the 300-char band — **Claude Code only** (see note) | `python3 scripts/check_listing_budget.py <root>` | 0 fits / 1 overflow / 2 unavailable |
| `check_desc_slim.py` | gates a description-slimming pass — kept text must stay verbatim, trigger spans must survive | `python3 scripts/check_desc_slim.py <before> <after>` | 0 clean / 1 unsafe |
| `eval_retrieval.py` | asks GLM (3× majority vote) whether the router can find each reference by its `when-to-read` scenario | `python3 scripts/eval_retrieval.py <skill_dir> --glm` | 0 clean / 1 misses |

> **The listing-budget check is Claude Code only.** It relies on Claude Code's shared skill-listing budget (≈1% of the model's context window; on overflow CC silently drops descriptions to name-only, and a name-only skill cannot auto-trigger). Codex has no equivalent budget mechanism, so this one check is skipped there. The other three scripts and every judgment dimension are cross-agent.

### What makes a description trigger

The single biggest lever on reliability — measured, not guessed ([Seleznov, 650 trials](https://medium.com/@marc.bara.iniesta/claude-skills-have-two-reliability-problems-not-one-299401842ca8)):

| Description form | Trigger rate |
| :--- | :--- |
| `"[What it does]. Use when [when]."` (Anthropic default) | ~50% |
| `"[Domain] expert. ALWAYS invoke when [trigger]. Do not [default] directly."` (Seleznov) | ~100% |

The counterintuitive part is the negative constraint (`Do not … directly`) — drop it and the rate collapses back to ~50%.

### Hard rules

A violation here is an error, not a suggestion.

| Rule | Source |
| :--- | :--- |
| description ≤ 1024 chars (Claude Code ≥ 2.1.105 accepts 1536) | Anthropic spec / CC release notes |
| listing-budget overflow is always reported — a population fact, fixed by a global pass, never by editing one skill | CC issues #56710 / #47627 |
| description in third person | Anthropic best practices |
| name uses only lowercase letters, digits, hyphens | Anthropic spec |
| body < 500 lines | Anthropic / community consensus |
| routing depth ≤ 2 hops (SKILL.md → index.md → file); nested indexes forbidden | structure-surgery |
| zero dangling routes, zero orphan subdocuments | structure-surgery iron rule |
| description on a single logical YAML line (no `>` or `|`) | Prettier reflow breaks it |
| every workflow step produces visible output | Seleznov experiment |
| a skill's claim about its own performance must point to in-repo evidence, or be cut | evidence-gating |

### Failure modes it names

The P-tier says how bad; the name says what kind.

- `[no-op]` — a line the model already obeys by default
- `[sediment]` — a stale line that drifted out of relevance
- `[sprawl]` — simply too long, even if every line is live
- `[duplication]` — the same meaning in more than one place
- `[premature-completion]` — an exit condition so vague the agent quits early
- `[weak-leading-word]` — an anchor word too weak to beat the model's default

### Priority tiers

| Tier | Meaning | Enters ❌ |
| :--- | :--- | :--- |
| **P0** | effect break (the flow doesn't connect when run) | always |
| **P1** | violates a structural hard rule | always |
| **P2** | insufficient specificity (no command, no I/O spec) | always |
| **P3** | readability | only when it changes what the next run does; else ⚠️ |

### Dimensions (loaded on demand by `when-to-read`)

`references/index.md` routes to all of these; only the ones whose condition fires get read.

| Reference | Covers |
| :--- | :--- |
| `description-templates.md` | trigger-strength template + listing-budget math |
| `body-quality-checklist.md` | body size and what to demote into references |
| `visible-output-rule.md` | every workflow step must print something |
| `yaml-pitfalls.md` | frontmatter formatting traps |
| `hard-code-vs-llm-judgment.md` | script it, or leave it to the model |
| `assets-vs-references.md` | sorting templates vs reference docs |
| `structure-surgery.md` | splitting, routing tiers, the 2-hop cap |
| `effect-dry-run.md` | walking one prompt through the workflow |
| `priority-tiers.md` | P0–P3 definitions and placement |
| `predictability-glossary.md` | the failure-mode vocabulary |
| `hard-rules.md` | the quantified must-pass rules |
| `exception-fallback.md` | what to do when a path or script errors |
| `language-policy.md` | English-by-default and its exceptions |
| `apply-safety.md` | size gate, pre-deletion check, closing the loop |
| `live-injection-check.md` | is the description actually injected this session |
| `rationale.md` | why the skill exists at all |

### Repository structure

```text
skill-doctor/
├── SKILL.md                              # the compass: diagnosis flow + routing
├── references/
│   ├── index.md                          # routes to every dimension by when-to-read
│   ├── apply-safety.md
│   ├── assets-vs-references.md
│   ├── body-quality-checklist.md
│   ├── description-templates.md
│   ├── effect-dry-run.md
│   ├── exception-fallback.md
│   ├── hard-code-vs-llm-judgment.md
│   ├── hard-rules.md
│   ├── language-policy.md
│   ├── live-injection-check.md
│   ├── predictability-glossary.md
│   ├── priority-tiers.md
│   ├── rationale.md
│   ├── structure-surgery.md
│   ├── visible-output-rule.md
│   └── yaml-pitfalls.md
├── scripts/
│   ├── check_routes.py                   # reachability / orphans / dangling / compass cap
│   ├── check_listing_budget.py           # description listing-budget (Claude Code only)
│   ├── check_desc_slim.py                # description-slimming gate
│   └── eval_retrieval.py                 # GLM routing-recall vote
├── assets/
│   └── hero.png
├── LICENSE
├── README.md
└── README.zh-CN.md
```

---

<div align="center">

> *A skill the model never triggers is just dead documentation.*

<br>

⭐ If skill-doctor caught a dead step in one of your skills, give it a star.

<br>

**Zane456** — author of [clear-chinese](https://github.com/Zane456/clear-chinese)

| Platform | Link |
| :--- | :--- |
| 🐙 GitHub | [@Zane456](https://github.com/Zane456) |

<br>

MIT License © [Zane456](https://github.com/Zane456)

</div>
