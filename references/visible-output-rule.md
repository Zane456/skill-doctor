# The Visible-Output-Per-Step Principle

## Core rule

**Any workflow step that defers output and produces no visible result is at risk of being silently skipped.**

Source: the Seleznov experiment (2026). Even after a skill has triggered and loaded, steps inside the body still get skipped by Claude — especially the ones that "execute silently". The failure mode is not a crash, it is **quiet omission that looks like completion**.

## Consequence

```
User: "help me check this SKILL.md"
Claude triggers skill-doctor, loads SKILL.md
[Step 1: read the target file - executed silently]
[Step 2: load references - executed silently]
[Step 3: output the diagnosis]
→ Claude jumps straight to Step 3, but it never actually read the references
→ the diagnosis output is made up from impression, not based on standards
```

## Fix pattern: every step must produce a print

```markdown
❌ Easily-skipped phrasing
## Step 1: Load the target SKILL.md
Read the SKILL.md being edited.

✅ Forced-visible phrasing
## Step 1: Load the target SKILL.md
Read the SKILL.md being edited, **print one line**:
[skill-doctor] Loaded: <path>  body=<N> lines  description=<M> chars
```

## Which steps are especially dangerous

| Step type | Risk | Fix |
|-----------|------|-----|
| Loading a file | high | print the file metadata (line count/size) after loading |
| Loading references | high | print "loaded references/X.md" |
| Internal checklist comparison | extreme | print each check's pass/fail |
| Computation/statistics | medium | print the computed result |
| Decision ("if X then…") | high | print "decision: X because Y" |

## Minimum standard

Each step prints at least 1 line with a `[skill-name]` prefix. The prefix lets the user grep the execution trace.

## Do not go to the other extreme

Visible per step ≠ flooding the screen per step. One step prints **1 line** of confirmation, not dumping all intermediate data.

## Exception

There is only one case where silence is allowed: the step's output **is what the user ultimately sees**, with no intermediate state to confirm. For example, the last step "apply the fix with Edit" — printing one line `Applied N fixes` is enough, no need to re-output the diagnosis conclusion (that is Step 3's job).

## How to use this when diagnosing

When skill-doctor reads this reference, it checks the target SKILL.md's multi-step workflow:

- [ ] Does every step explicitly require producing visible output?
- [ ] Do steps that load a file / references require printing the metadata?
- [ ] Do decision steps require printing the conclusion + basis?
- [ ] Does the status prefix carry `[skill-name]` for easy grep?
