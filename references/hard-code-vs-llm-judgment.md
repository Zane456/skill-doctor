# Hard-coding vs LLM Judgment: When to Move a Section to scripts/

## The core decision

```
mechanically deterministic → scripts/<name>.py
needs judgment             → SKILL.md body or references/
```

Do not split by "it looks repetitive" — split by "will it drift".

## Drift risk (intent drift)

The failure mode of LLM workflows: SKILL.md says "this skill will do X", but when Claude actually executes it merely says it did X. **A predictive statement ≠ actual behavior.**

- If an operation **has an objective right answer** ("is it ≤ 1024 characters", "does the name match the regex"), the LLM will occasionally make something up. This **must be scripted** as a gate.
- If an operation **needs semantic judgment** ("is this section bloat", "which section belongs in references"), a script cannot be written for it. This **must be left to the LLM**.

## Signals it should be scripted

✅ Move the section to `scripts/` when **any one** of the following holds:

1. **It can be written as a regex / character count / AST parse**
   - regex match `^[a-z0-9-]+$`
   - char count / line count / word count
   - YAML frontmatter parsing

2. **Wrong is just wrong** — there is no "depends on the situation" gray zone
   - Is the description ≤ 1024? It either is or it isn't
   - Did the path use `\`? It either did or it didn't

3. **Repeatedly occurring boilerplate** (a script can run it deterministically, instead of having the LLM regenerate it)
   - PDF rotation / field extraction / file packaging

4. **A critical safety / validation gate** — skipping it causes loss
   - "must back up before modifying a file"
   - "must pass lint before committing"

## Signals it should not be scripted

❌ Leave it to the LLM when **any one** of the following holds:

1. **"It depends on context"**
   - Is this section bloat? Depends on skill type, reader, purpose
   - Is this name descriptive enough? Depends on what the skill does

2. **The judgment needs semantic understanding**
   - Does the description have a negative constraint? Look at the meaning, not the literal text
   - Should a body section be split? Weigh multiple factors

3. **A suggestion rather than a check**
   - "suggest renaming to X" — the LLM does this better than a script
   - "suggest moving this section to references/Y" — same

4. **Rarely triggered or not repeated**
   - Something done once and over with — do not build a script for it

## One gray boundary: scriptable but not necessarily worth it

**Single-file line/char counts** — scriptable (grep / wc), but the LLM can also do it (it sees line numbers via Read). Judge by script cost vs on-the-spot reliability; if the LLM miss probability is > 5%, script it.

**Population-level facts always cross the threshold.** An in-context LLM cannot know the other 60 installed skills without reading 60 directories — so the listing-budget check is `scripts/check_listing_budget.py`, link/orphan/conservation checks are `scripts/check_routes.py`, and retrieval testing is `scripts/eval_retrieval.py`. These three are skill-doctor's deterministic gates; everything semantic stays with the LLM.

## Judgment when diagnosing a target SKILL.md

When skill-doctor sees a section of the target SKILL.md saying "this skill will do X", categorize it by the table below:

| Action the section describes | Verdict |
|------------------------------|---------|
| "parse YAML / check fields" | should be a script, not the LLM |
| "run lint / validate" | should be a script |
| "judge whether this section is bloat" | should be the LLM, not a script |
| "rewrite the description so triggering is more stable" | should be the LLM, not a script |
| "render a chart / convert a file format" | should be a script |
| "explain / discuss / suggest" | should be the LLM |

Report format:

```
⚠️ Suggested improvements
  - the "YAML field validation" described in body lines 45-60 should be implemented as scripts/validate_frontmatter.py
    Why: mechanical judgment, no room for judgment, the LLM occasionally misses it
    How: write a 30-line Python script, change the body to "run scripts/validate_frontmatter.py"
```

## The reverse trap

**Do not hard-code just to hard-code.** If a check is done reliably by the LLM after reading references, let the LLM do it — one more script means one more piece of code debt.

## Auditing a target's existing scripts/

When the target skill ships `scripts/`, the doctor audits them mechanically (this dimension is what catches "confidently wrong numbers" from a buggy gate):

1. `python3 -m py_compile <script>` (or a `--help` / dry-run invocation) — does it even run?
2. Does the body's invocation match the script's actual argv (flags, arg order, quoting of paths with spaces)?
3. Hardcoded absolute paths / another machine's layout? (breaks on any other install)
4. Do exit codes carry distinct meanings, and does the body tell the model what each means?
5. Does it fail loudly (helpful message) rather than printing a plausible wrong answer?
