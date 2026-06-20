# Getting Started — first-time setup (agent-driven)

This file is **instructions for the AI agent**, not a script for a human to run in a
terminal. Most people use skill-doctor from a chat box (Claude Code, Codex, Hermes,
OpenClaw), where stdin prompts don't work. So the agent drives setup **as a
conversation**: it explains what this is, detects the platform, asks the few choices
in plain language, and does the install with its own file tools.

> **To the user:** just say *"set up skill-doctor"* (or *"安装一下 skill-doctor"*).
> The agent walks you through it. When it's done, you can delete this file — it
> never runs on its own and won't pop up again.

---

## Agent: run these steps, one visible message per step. Use plain words — assume the user has never used this skill and does NOT know any internal terms.

### Step 0 — Say what skill-doctor is (2 lines, plain)
Before asking anything, tell the user in one or two plain sentences, e.g.:
*"skill-doctor checks your other skills so the AI actually triggers them — it finds
descriptions that won't fire, references the model can't locate, and a layout that
needs splitting, then suggests fixes. Let me get it set up."*
Do NOT use internal jargon ("Level 1/2", "routing recall", "listing budget") in
anything the user reads — describe the effect instead.

### Step 1 — Detect the platform
Run the non-interactive detector and tell the user, in plain words, what it found:
```bash
python3 scripts/detect_platform.py
```
- 0 platforms found → ask which agent they use (Claude Code / Codex / Hermes /
  OpenClaw) and its model; carry that forward manually.
- 1+ found → e.g. *"You're on Claude Code. I'll install into your skills folder."*

### Step 2 — Ask the install choices (in chat, plain language)
1. **Which platform(s)** to install into, only if more than one was detected.
2. **Copy or link?** — *"Copy makes a standalone install (deleting this folder
   later won't break it — recommended). Linking keeps it tied to this folder so
   edits here take effect live."*

### Step 3 — Install into the chosen skills folder
Use the `install_target` from Step 1 for each chosen platform (folder name
`skill-doctor`). Install `SKILL.md`, `references/`, and `scripts/` — **not**
`__pycache__`, README files, this file, or `.git`.
- Copy: create `<install_target>/skill-doctor/` and copy the three items in.
- Link: symlink the folder (or per-item) into `<install_target>/skill-doctor`.
Confirm in one line: *"Installed to `<path>`."*

### Step 4 — Offer the optional AI-powered check (no jargon, state the cost)
Frame it by what it does, not by a level number:
*"Want to turn on a deeper check? It uses an AI model to actually test that the AI
will pick the right help-file for each task — it catches confusable wording the
free check can't. It costs almost nothing: one run is roughly tens of thousands of
tokens (a few cents on a paid key like DeepSeek, free on a free provider). It needs
an API key. Skip it and everything else still works fully."*

- **No** → skip; say the standard checks all still run with zero setup.
- **Yes** → collect base URL / model / key, write them to a local `.env` in the repo
  (already gitignored):
  ```
  EVAL_LLM_BASE_URL=https://api.deepseek.com
  EVAL_LLM_MODEL=deepseek-v4-flash
  EVAL_LLM_API_KEY=sk-...
  ```
  Then say plainly: the key lives only in this local `.env`, skill-doctor never logs
  it, commits it, or sends it anywhere except the base URL you set; `.env` is
  gitignored so it won't be pushed.

### Step 5 — Context window note (only if Step 1 said "unknown")
If the platform's context window came back unknown, tell the user the budget check
needs it; ask (200k? 1M?) or have them set it in the platform's own config. Without
it, that one check is skipped — everything else still runs.

### Step 6 — Done, and this file is disposable
Confirm: *"✅ skill-doctor is installed at `<path>`. The optional AI check is
on / off. You can delete `GETTING_STARTED.md` now — setup is one-time and this file
never triggers by itself."*
