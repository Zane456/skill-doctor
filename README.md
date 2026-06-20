English | [简体中文](README.zh-CN.md)

<div align="center">

# skill-doctor

<p align="center">
  <img src="assets/hero.png" alt="skill-doctor — health check for AI agent skills: diagnose SKILL.md trigger reliability, routing recall, and package structure" width="760" />
</p>

> *"A skill the model never triggers is just dead documentation."*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/works_on-Claude_Code_·_Codex_·_Hermes_·_OpenClaw-blueviolet.svg)]()
[![Checks](https://img.shields.io/badge/checks-4%20deterministic-blue.svg)]()
[![Type](https://img.shields.io/badge/type-meta--skill-green.svg)]()

<br>

**Diagnose, routing-test, and restructure your agent skills — so the model actually triggers them.**

<br>

skill-doctor audits a `SKILL.md` the way an LLM actually reads it. Spec linters stop at frontmatter and broken links. skill-doctor scores how reliably a skill triggers, runs a routing-recall test on every reference file, names the failure mode, and rewrites the package layout when the routing breaks. Deterministic scripts carry the core checks, none of them needs an API key, and it works across Claude Code, Codex, Hermes, and OpenClaw.

<br>

[See It in Action](#see-it-in-action) · [Up and Running](#up-and-running) · [By the Numbers](#by-the-numbers) · [How It Works](#how-it-works)

</div>

---

## See It in Action

Point it at a skill and it prints a diagnosis, not a grammar report:

```text
[skill-doctor] Auditing: my-skill/SKILL.md   body=142 lines   description=64 chars
[skill-doctor] Budget (claude_code): 38 skills, 31k vs ≈40k → fits

[skill-doctor] Diagnosis

❌ Must fix (P0→P3)
  [P0 effect break]    Step 3 reads a file Step 1 never writes → the workflow dead-ends
  [P1 trigger]         description has no negative constraint → trigger rate ~50%, not ~100%
  [weak-leading-word]  body opens with "This skill helps you..." → a no-op line the model skips

⚠️ Suggested
  - references/tips.md mixes 3 unrelated topics → split by topic, one file each

✅ Passed
  - routing: 2 hops, 0 orphans, 0 dangling links
  - 17 references reachable from SKILL.md
```

It does not check your Markdown grammar. It tells you the model will silently skip Step 3, and that your description fires about half the time, then says exactly why.

---

## Up and Running

**Easiest — let the agent set it up.** Clone the repo, open it in your agent (Claude Code / Codex / Hermes / OpenClaw), and say *"set up skill-doctor"*. It detects your platform, installs into the right skills folder, and offers the optional LLM check. The flow lives in [GETTING_STARTED.md](GETTING_STARTED.md) — delete it once setup is done.

**Manual** — a skill installs by living in your skills folder:

```bash
git clone https://github.com/Zane456/skill-doctor.git ~/.claude/skills/skill-doctor
# Codex / OpenClaw: ~/.agents/skills/skill-doctor   ·   Hermes: ~/.hermes/skills/skill-doctor
```

The scripts run on Python 3 with zero dependencies. Every core check — routing, budget, structure — needs **no API key**.

**Optional — a deeper, AI-powered check.** Beyond the free checks, skill-doctor can ask an LLM to actually test that the model picks the right reference for each task — catching confusable wording the keyword pass can't. It costs almost nothing: one run is roughly tens of thousands of tokens — a few cents on a paid key, free on a free provider. Bring your own key for any OpenAI-compatible provider:

```bash
export EVAL_LLM_BASE_URL=https://api.deepseek.com   # DeepSeek shown; Groq / OpenRouter / Gemini / z.ai all work
export EVAL_LLM_MODEL=deepseek-v4-flash             # the cheap one
export EVAL_LLM_API_KEY=sk-...                      # from platform.deepseek.com
```

Your key is read from the environment at runtime only — skill-doctor never stores, logs, or commits it, and sends it nowhere except the base URL you set (`.env` is gitignored).

Then ask your agent to review a skill — *"audit this SKILL.md"* / *"审查这个 skill"* — or invoke `skill-doctor` directly.

---

## By the Numbers

Every claim below traces to a script or a reference file in this repo.

| Feature | What you get |
| :--- | :--- |
| **Deterministic scripts** | 4 checks — routing, listing-budget, structure, description-slim — no LLM, exit codes you can wire into CI |
| **Trigger template** | The Seleznov 3-part description form lifts trigger rate from ~50% to ~100% (650-trial study) |
| **Routing-recall test** | An LLM (any OpenAI-compatible, optional) votes 3× per reference file; a majority decides whether each doc is uniquely findable |
| **Failure-mode taxonomy** | 6 named modes — `no-op` / `sediment` / `premature-completion` / `sprawl` / `weak-leading-word` / `duplication` |
| **Structure surgery** | Enforces a hard 2-hop routing cap, splits files verbatim, leaves 0 orphans |
| **Listing-budget guard** | Measures installed descriptions against each platform's listing budget — **Claude Code, Codex, Hermes, OpenClaw** (see note) |
| **Compass cap** | SKILL.md ≤ 6000 chars; this skill's own 18 references load on demand |

> **Note — the listing-budget check is platform-aware.** Every supported platform injects each skill's name+description into the system prompt under a budget and degrades on overflow; only the constant differs — Claude Code ~1% of context (silent name-only truncation), Codex ~2% or 8000 chars (shortens then omits with a warning), OpenClaw a `maxSkillsPromptChars` cap, Hermes measured straight from its injected-prompt snapshot. `detect_platform.py` picks the right rule; if the platform or context window is unknown, the script asks you. The other three scripts and every judgment dimension are cross-agent.

---

## How It Works

skill-doctor runs a fixed diagnosis flow, and every step prints a line — a step with no visible output is a step the model silently skips.

```text
SKILL.md + references/ + scripts/
        |
        v
   skill-doctor
        |
   |-- deterministic scripts   (detect · routes · budget · slim)
   |-- LLM routing-recall       (optional · vote 3x per file)
   |-- judgment dimensions      (trigger · failure modes)
        |
        v
   P0-P3 diagnosis  +  named failure mode
        |
        v
   apply after you confirm  ->  re-verify routing
```

**1. Read and budget** — reads the whole SKILL.md, then counts every installed description against the listing budget, so it judges one skill knowing the crowd it competes with.
**2. Load only what fires** — pulls in a quality dimension only when its `when-to-read` line matches, the same lazy-loading it asks of the skills it audits.
**3. Dry-run one real prompt** — walks a typical prompt through the body steps; if Step 3 needs an input no earlier step produced, that is a P0 effect break.
**4. Report, then name it** — prints a P0–P3 list and tags each finding with its failure mode, so "written badly" becomes "this line is a no-op."
**5. Fix and re-verify** — after you confirm, it applies the edit and re-runs `check_routes.py`; a restructure is never called done while routing still fails.

---

## What's Inside

```
skill-doctor/
├── GETTING_STARTED.md                  # one-time, agent-driven setup (deletable after)
├── SKILL.md                            # the compass — routes to everything
├── references/                         # 18 on-demand dimensions and policies
│   ├── index.md                        # the reference router (when-to-read + keywords)
│   ├── description-templates.md        # trigger-strength template + listing-budget math
│   ├── body-quality-checklist.md       # when the body is too long, what to demote
│   ├── visible-output-rule.md          # every workflow step must print something
│   ├── yaml-pitfalls.md                # frontmatter formatting traps
│   ├── hard-code-vs-llm-judgment.md    # script it, or leave it to the LLM
│   ├── assets-vs-references.md         # sorting templates vs reference docs
│   ├── structure-surgery.md            # split / restructure / route, 2-hop cap
│   ├── effect-dry-run.md               # walk one prompt through the workflow
│   ├── priority-tiers.md               # P0–P3 severity definitions
│   ├── predictability-glossary.md      # the named failure modes
│   ├── hard-rules.md                   # the quantified must-pass rules
│   ├── exception-fallback.md           # what to do when something errors
│   ├── language-policy.md              # English-by-default policy
│   ├── apply-safety.md                 # size gate, pre-deletion check, close the loop
│   ├── live-injection-check.md         # is the description actually injected
│   ├── output-style.md                 # how skill-doctor talks to the human
│   └── rationale.md                    # why this skill exists
└── scripts/                            # deterministic checks, no dependencies
    ├── detect_platform.py              # which platform + its listing-budget rule
    ├── check_routes.py                 # reachability, orphans, 6000-char cap
    ├── check_listing_budget.py         # description budget (CC · Codex · Hermes · OpenClaw)
    ├── eval_retrieval.py               # optional LLM routing-recall vote (BYOK)
    └── check_desc_slim.py              # safe description-slimming gate
```

MIT — use it, fork it, ship it.

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
