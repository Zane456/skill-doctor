# Effect Dry-Run (Effect Coherence Walkthrough)

An ailment that pure structural review cannot catch: the format is all correct, but the flow does not connect when it runs. The dry-run is a low-cost backstop — it does not actually spawn a sub-agent, it just simulates one run in your head.

## When to do it

- Any SKILL.md containing a workflow / Phase / Step
- When the trigger words clearly mismatch the body workflow
- After a round of fixes, to confirm "the form is right and the effect connects too"

## Procedure

### 1. Take the single most common prompt

Not an edge case — the first sentence the user would **most likely** say when using this skill.

Example: skill-doctor itself → "help me review this SKILL.md"
Example: proofreading → "proofread this text"
Example: darwin-skill → "optimize all skills"

### 2. Walk through the body once

Following the SKILL.md's Step / Phase order, ask 3 questions at each step:

1. **Can the input be obtained from the previous step?** — no source to find = broken link
2. **Is the instruction specific enough to execute?** — "process the image" does not count, "convert to PNG with sips" does
3. **Can the output feed the next step?** — the output format of step N must be acceptable to step N+1

### 3. Mark the problems

If you find any broken link / ambiguity / mismatch, mark P0 (effect problem, must fix).

Walking through successfully is not proof of correctness, only "no problem spotted so far".

## What not to do

- Do not actually spawn a sub-agent to run it — that is darwin-skill's job, the doctor only does the dry-run
- Do not run multiple prompts — 1 most typical one is enough, more is darwin's test-prompts.json
- Do not use dry-run results for scoring — the doctor does not score, it only marks P0/P1/P2/P3

## Example: running a dry-run on skill-doctor

prompt: "help me review this SKILL.md, path is ~/x/SKILL.md"

- Step 1 reads and prints the body line count → ✅ input is clear, body line count feeds the Step 4 size gate
- Step 2 selects references by table → ✅ table conditions are specific
- Step 2.5 dry-run (this step itself) → ✅ stops at 1 level of recursion, no further nesting
- Step 3 outputs the diagnosis (with P0-P3 priorities) → ✅ template is strict
- Step 4 size gate + Edit → ✅ waits for user confirmation

Connects. If Step 2's table only said "select as appropriate", it would break the link at that step — that is a P0.
