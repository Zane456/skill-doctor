# Live-injection check (Step 2.6 detail)

Detail for SKILL.md **Step 2.6** (only when the target skill is in the current session's scope). The body keeps the action and the print line; the cases are here.

The current session's own available-skills list is ground truth for the budget mechanism — check whether the target skill appears there **with its description**:

- name + description visible → injected, pass
- **name only** → it is being budget-dropped right now: report it prominently at the top of the Step 3 diagnosis as a **population-level notice** (the description never reaches the model, so auto-triggering cannot happen). Cause = global pool overflow, not this skill's text — do NOT shorten this skill to fix it; the levers (global slimming / `skillListingBudgetFraction`) are the user's call, listed in `references/description-templates.md` §"character budget"
- skill not in this session's scope (another project's skill), or its description was created/edited **in this session** (the list only refreshes on session start) → skip with reason
- **platform can't expose its own skills listing to the model** (Codex / Hermes / OpenClaw, anything but Claude Code) → skip with reason "non-CC platform: listing not readable in-session". The listing-budget *numbers* still come from `check_listing_budget.py` (it reads the filesystem), but this in-session injected/dropped check is Claude-Code-only
