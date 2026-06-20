English | [简体中文](README.zh-CN.md)

<div align="center">

# skill-doctor

<img src="assets/hero.png" alt="skill-doctor — a health check for AI agent skills: trigger reliability, routing, package structure" width="640" />

**A health check for AI agent skills — so the model reliably triggers, reads, and routes through the skills you write.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Works on](https://img.shields.io/badge/works_on-Claude_Code_·_Codex_·_Hermes_·_OpenClaw-blueviolet.svg)]()
[![Core checks](https://img.shields.io/badge/core_checks-no_API_key-2ea44f.svg)]()

</div>

---

## Features

- **Skills that actually get used** — it audits how your skill is described so the model triggers it when it should, instead of leaving it installed and ignored.
- **Nothing eats your context** — it finds what runs too long or needs splitting, so the model reads the whole thing and lands on the right part instead of giving up halfway.
- **Stable and free to run** — the core checks don't depend on the model's mood and need no API key; run the same skill twice and the verdict matches.
- **It tells you what to fix, why, and how** — you get a priority-sorted list of real problems with concrete fixes, not a vague score.
- **Same on every platform, and it never touches your files first** — Claude Code, Codex, Hermes, and OpenClaw all run it the same way, and it always asks before editing.

---

## What It Is

skill-doctor is a skill that gives your other skills a health check. You write a skill, but you can't tell whether the model will trigger it when it should, read the body in full, or find the right reference file — and these failures never throw an error, so you never notice them. skill-doctor finds them one by one, sorts them by severity, explains why each one is a problem and how to fix it, and edits your files only after you say so. It's for anyone who writes their own skills.

---

## See It in Action

```
You: check this skill for me

skill-doctor:

Health check done — 3 problems:

1. The description runs 1,100 characters — too long
   → it loads into context every time and eats your budget;
     a few hundred characters is plenty

2. SKILL.md is 680 lines — over the limit
   → move some detail into references/ so it loads on demand,
     instead of being read in full every time

3. One file in references/ is never reached (an orphan)
   → wire it into the routing, or delete it

Want me to fix these? (I won't touch your files until you say so)
```

---

## Repository Structure

```text
skill-doctor/
├── SKILL.md                          # the compass: diagnosis flow + routing
├── GETTING_STARTED.md                # one-time agent-driven setup (delete after)
├── references/                       # judgment dimensions, loaded on demand
│   ├── index.md                      # routes to every dimension by when-to-read
│   ├── apply-safety.md               # size gate, pre-deletion check, closing the loop
│   ├── assets-vs-references.md       # sorting templates vs reference docs
│   ├── body-quality-checklist.md     # body size and what to demote into references
│   ├── description-templates.md      # trigger-strength template + listing-budget math
│   ├── effect-dry-run.md             # walking one prompt through the workflow
│   ├── exception-fallback.md         # what to do when a path or script errors
│   ├── hard-code-vs-llm-judgment.md  # script it, or leave it to the model
│   ├── hard-rules.md                 # the quantified must-pass rules
│   ├── language-policy.md            # English-by-default and its exceptions
│   ├── live-injection-check.md       # is the description actually injected this session
│   ├── output-style.md               # how skill-doctor talks to the human
│   ├── predictability-glossary.md    # the failure-mode vocabulary
│   ├── priority-tiers.md             # P0–P3 definitions and placement
│   ├── rationale.md                  # why the skill exists at all
│   ├── structure-surgery.md          # splitting, routing tiers, the 2-hop cap
│   ├── visible-output-rule.md        # every workflow step must print something
│   └── yaml-pitfalls.md              # frontmatter formatting traps
├── scripts/                          # deterministic checks, no LLM (except eval_retrieval)
│   ├── detect_platform.py            # which platform + its listing-budget rule
│   ├── check_routes.py               # reachability / orphans / dangling / compass cap
│   ├── check_listing_budget.py       # listing-budget across platforms
│   ├── check_desc_slim.py            # description-slimming gate
│   └── eval_retrieval.py             # optional LLM routing-recall vote (bring your own key)
├── assets/
│   └── hero.png                      # README hero image
├── LICENSE                           # MIT
├── README.md                         # this file (English)
└── README.zh-CN.md                   # Chinese version
```

---

## Install

**Easiest — let the agent install it.** Clone the repo, open it in your agent (Claude Code / Codex / Hermes / OpenClaw), and say *"set up skill-doctor"*. It detects your platform, installs into the right skills folder, and you can delete `GETTING_STARTED.md` afterward.

**Manual** — a skill installs by living in your skills folder:

```bash
git clone https://github.com/Zane456/skill-doctor.git ~/.claude/skills/skill-doctor
# Codex / OpenClaw: ~/.agents/skills/skill-doctor    Hermes: ~/.hermes/skills/skill-doctor
```

The scripts run on Python 3 with no dependencies, and the core checks need no API key. To turn on the optional, deeper AI check, point it at any OpenAI-compatible provider with your own key:

```bash
export EVAL_LLM_BASE_URL=https://api.deepseek.com
export EVAL_LLM_MODEL=deepseek-v4-flash
export EVAL_LLM_API_KEY=sk-...
```

<div align="center">

MIT License © [Zane456](https://github.com/Zane456)

</div>
