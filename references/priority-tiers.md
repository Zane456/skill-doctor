# Priority Tiers (P0-P3)

The skill-doctor diagnosis sorts the **Code layer** P0→P3. This file gives the definitions and placement rules.

## Definitions

| Tier | Meaning | Severity | Typical example |
|------|---------|----------|-----------------|
| **P0** | Effect break | always a finding | dry-run finds an ambiguous instruction that does not connect, mismatched output, a flow that cannot close the loop |
| **P1** | Violates a structural hard rule | always a finding | description >1024 chars, name contains uppercase, frontmatter not parseable, broken citation links (path not found), unclosed markdown tags |
| **P2** | Insufficient specificity | always a finding | step has no concrete parameters, missing input/output spec, missing exception fallback |
| **P3** | Readability | **finding only when it affects execution**; otherwise drops to Low (cosmetic) | see below |

## P3 placement rule (core)

P3 is the only tier whose weight depends on a judgment. To decide, ask 1 question:

> If this is not fixed, will the next LLM running this skill do something wrong?

- **Yes** → a real Code-layer finding, mark P3 (e.g. misnumbered steps cause the LLM to skip a step, Markdown formatting causes a trigger word to be swallowed by the parser)
- **Merely verbose / ugly / repetitive** → **Low** (lowest in the Code layer; in the decision layer it lands in ✅ Safe to fix now, or is simply noted — e.g. a slightly long paragraph, repeated phrasing, missing TL;DR)

This rule exists so the P0–P2 tiers are not diluted by decorative problems — those tiers should be the signal of "if not fixed, it crashes". Note that any broken citation links (path not found) or unclosed markdown tags are NOT subject to P3's subjective judgment; they are hard structural errors and must be classified as **P1**.

## Using the priorities

The P-tier rides in the **Code layer** of the report; the report shape (Code layer → ✅/🤔 decision layer) is defined in `output-format.md`. The P-tier says *how bad*; which decision bucket (✅ Safe to fix now / 🤔 Needs your decision) a finding lands in is decided separately there — independent axes (a P0 with a 🟢 fix is a "Safe to fix now" item).

Sorting rule: within the Code layer, strictly P0 → P1 → P2 → P3. Within the same tier, ascending by file line number.
