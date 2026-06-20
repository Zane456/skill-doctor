# Predictability Glossary (skill quality vocabulary)

Imported and adapted from `mattpocock/skills` → `writing-great-skills/GLOSSARY.md`.
The other references check a skill's **form** (size, routing, triggers, visible
output); this one checks whether the body **earns its predictability**. Use these
names in the Step 3 report so a defect is pointable, the way a circuit fault is named.

**Root virtue — Predictability.** A skill exists to wrangle determinism out of a
stochastic model: the agent takes the same *process* every run, not the same output
(a brainstorming skill should predictably diverge). Every term below is a lever on it.
Cost and maintainability are symptoms of predictability, not rivals to it.

## Net-new checks (skill-doctor had no explicit dimension for these)

### No-op
A line the model already obeys by default → you pay context load to say nothing.
**Test:** does this line change behaviour *versus the model's default*? If deleting it
changes nothing, it is a no-op. It is **model-relative, not reader-relative** — two
people who disagree are disagreeing about the default; settle it by running the skill,
not by debate. Hunt **sentence by sentence**; when a sentence fails, delete the whole
sentence, do not trim words from it. Be aggressive.
- **Tier:** ⚠️ (pure token waste); **P3** only if the dead instruction also misleads.
- **Wiring (important):** a no-op is a deletion *candidate* only. Route every candidate
  that is a rule / branch / condition through **SKILL.md Step 4's pre-deletion check**
  before removing. A true no-op has zero dependent prompts, so the gate clears it as a
  dead-branch; if the gate finds a hitting prompt, it was never a no-op. The two halves
  compose — this reference finds candidates, Step 4 confirms the cut.

### Relevance & Sediment
**Relevance** — does this line still bear on what the skill does? It loses relevance by
never bearing on the task (mere exposition) or by going **stale** (the behaviour or
world it describes drifted). **Sediment** is the accumulation of those stale layers,
because adding feels safe and removing feels risky — the default fate of any skill with
no pruning pass. **Distinct from no-op:** relevance asks whether a line *bears on the
task*; no-op asks whether it *changes behaviour*. A line can be relevant and a no-op.
- **Tier:** **P3** if a stale line now misleads the next agent; otherwise ⚠️.

### Completion criterion & Premature completion
Every workflow step ends on a **completion criterion** — the condition telling the
agent the work is done. Two axes, each a separate lever:
- **Clarity** — can the agent tell done from not-done? A vague bound ("understanding
  reached") invites **premature completion**: the agent declares done and slips to the
  next step. *Between-steps failure — needs steps to bite, so check only when the body
  has a workflow.*
- **Demand** — how much it requires ("every modified file accounted for" vs "produce a
  change list"). Sets how much **legwork** the agent does. *Not step-bound — it also
  binds flat reference ("every rule applied"), so check it even on a pure-reference
  skill.*

- **Tier:** a missing / vague criterion that lets the agent quit early is **P2** (missing
  exit spec); cosmetic vagueness ⚠️.
- **Defence order to recommend:** sharpen the criterion first (cheap, local); only if it
  is irreducibly fuzzy *and* the rush is observed, split the sequence to hide later steps.
- **Overlap note:** the clarity axis overlaps `effect-dry-run.md`'s "is the instruction
  specific enough"; the **demand axis** is the genuinely net-new check.

### Leading word
A compact concept already in the model's pretraining that the agent thinks with while
running the skill — repeated as a *token*, never re-explained as a sentence, it
accumulates a distributed definition and anchors a region of behaviour in the fewest
tokens by recruiting priors the model already holds. Serves predictability twice: in
the body it anchors *execution* (same behaviour each time the word appears); in the
description it anchors *invocation* (a word the user actually types links their prompts
to the skill).
- **Adaptation for this user — technical-concept words only, no metaphor class.** This
  repo's owner bans metaphor/analogy. ✅ `tight` loop, `red`/`green`, `idempotent`,
  `relentless`. ❌ `fog of war`, `tracer bullets` (metaphor — drop, even though the
  upstream glossary lists them).
- **Crosses no-op:** a leading word too weak to beat the default *is a no-op* (`be
  thorough` when the agent is already thorough-ish) → fix is a stronger word
  (`relentless`), not a different technique.
- **Tier:** ⚠️ / P3 optimisation, unless a weak word leaves the agent under-performing a
  required behaviour.

## Already covered — name them, do not re-define (single source of truth)

- **Duplication** — the same meaning in more than one place. Inflates that meaning's rank
  on the information ladder past its worth. Already handled by `body-quality-checklist.md`
  ("information lives in exactly one place"). Just label it `[duplication]`.
- **Sprawl** — a skill simply too long, even when every line is live and unique (distinct
  from sediment's stale length and duplication's repeated length). Already handled by
  `body-quality-checklist.md` (size / splitting) + `structure-surgery.md` (disclose
  reference behind pointers, split by branch / sequence). Just label it `[sprawl]`.

## Using these in the diagnosis

The failure mode says *what kind* of defect; P0–P3 says *how bad*. The two axes are
**orthogonal** — these names never replace a tier, they prefix it. In Step 3, tag a
finding with its name so the user can act on it precisely, e.g.
`[no-op]`, `[sediment]`, `[premature-completion]`, `[weak-leading-word]`,
`[duplication]`, `[sprawl]`. Assign the tier by `priority-tiers.md`'s rule ("if unfixed,
will the next LLM running this skill do something wrong?").
