# Priority Tiers (P0-P3)

The skill-doctor diagnosis sorts the ❌ section P0→P3. This file gives the definitions and placement rules.

## Definitions

| Tier | Meaning | Condition to enter ❌ | Typical example |
|------|---------|----------------------|-----------------|
| **P0** | Effect break | always | dry-run finds an ambiguous instruction that does not connect, mismatched output, a flow that cannot close the loop |
| **P1** | Violates a structural hard rule | always | description >1024 chars, name contains uppercase, frontmatter not parseable, broken citation links (path not found), unclosed markdown tags |
| **P2** | Insufficient specificity | always | step has no concrete parameters, missing input/output spec, missing exception fallback |
| **P3** | Readability | **only when it affects execution**; otherwise goes in ⚠️ | see below |

## P3 placement rule (core)

P3 is the only tier that crosses sections. To decide, ask 1 question:

> If this is not fixed, will the next LLM running this skill do something wrong?

- **Yes** → ❌ section, mark P3 (e.g. misnumbered steps cause the LLM to skip a step, Markdown formatting causes a trigger word to be swallowed by the parser)
- **Merely verbose / ugly / repetitive** → ⚠️ section (e.g. a slightly long paragraph, repeated phrasing, missing TL;DR)

This rule exists so the ❌ section is not diluted by decorative problems — ❌ should be the signal of "if not fixed, it crashes". Note that any broken citation links (path not found) or unclosed markdown tags are NOT subject to P3's subjective judgment; they are hard structural errors and must be classified as P1 in the ❌ section.


## Using the priorities

Diagnosis report:

```
❌ Must fix (sorted P0→P3)
  [P0 ...] ...
  [P1 ...] ...
  [P2 ...] ...
  [P3 affects execution] ...   ← only P3 items that meet the "will do something wrong" rule

⚠️ Suggested improvements (including purely cosmetic P3)
  - ...
```

Sorting rule: within the ❌ section, strictly P0 → P1 → P2 → P3. Within the same tier, ascending by file line number.
