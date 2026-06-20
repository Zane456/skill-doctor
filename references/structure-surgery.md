# Subdocument Structure Surgery (absorbed from the retired skill-structure skill)

Restructure a skill's subdocument layer (`references/`, `scripts/`, `assets/`) and its
routing. Enter this dimension when: a reference file is too long, one document mixes
2–3 distinct topics, routing between SKILL.md and subdocuments is unclear, or
`check_routes.py` reports orphans/dangling links.

## Organize before you split (least to most invasive — take the first that resolves it)

1. **Append** to an existing themed file when the theme matches.
2. **Rename** for clarity (`git mv`), then fix SKILL.md routing and every back-reference.
3. **Split** a fat or mixed file into themed siblings; update routing.
4. **Merge** near-duplicate files; no dangling references left behind.
5. **Promote** multi-step operation content into a dedicated `<operation>_workflow.md`.

Escalate to a new sibling *skill* only when organizing inside the current skill still
leaves the responsibility boundary unclear.

## The two fission cases (split by structure, never by byte count alone)

- **Case A — oversized single-topic doc** (an article, e.g. past ~12 KB) → split **by its
  own sections**, one section-cluster per file, named after the subtopic.
- **Case B — mixed doc** (2–3 unrelated topics, ANY size) → split **by topic**, one file
  per topic, each routed.

Size signals (soft ~8 KB / hard ~12 KB for references; ~200/~500 lines for scripts).
**Exemption**: lookup catalogs / generated indexes that are searched, never read
end-to-end — completeness sets their size; do not fragment them.

Naming: `snake_case`, name states purpose (`<topic>.md`, `<operation>_workflow.md`,
`<source>_error_signatures.md`, `by-<axis>.md`). Never create catch-alls
(`learned_rules.md`, `tips.md`, `notes.md`, `pitfalls.md`) — they accumulate mixed topics.

## Routing tiers (escalate only when the compass budget forces it)

Hard line: **SKILL.md ≤ 6000 chars**. Everything else is a soft signal.

1. **Flat** — direct routing table in SKILL.md (≤ ~5 cohesive files).
2. **Grouped** — routes under 2–4 topic subheadings, still in SKILL.md (~6–10 files).
3. **Wiki-index** — `references/index.md`, SKILL.md keeps one pointer row (many files,
   or inline listing would blow the 6000-char cap).

When two tiers seem plausible, pick the simpler. Branching readers (different
references by condition) → every route row MUST carry a `when-to-read` condition.

## Index format — and the 2-hop hard cap

Each index entry: file link + one-line "covers what" + `when-to-read:` + `keywords:`.
Keywords carry the searchable surface; keep the blurb to one sentence.

**HARD RULE — maximum routing depth is 2 hops: SKILL.md → references/index.md → file.**
A nested index (index → sub-index → file) is forbidden: measured in practice, the
third hop is where LLM recall dies — the model stops at the middle layer or picks the
wrong sub-index, with no error. If a single index grows past the soft cap, that is
evidence the *skill* is too big — split the skill, don't deepen the tree.
(This hardens the retired skill-structure's "single layer first" from advice to law.)

## Iron rules (a violation is an error)

1. **Content conservation** — splitting is verbatim relocation. Only headings, routing
   rows, and one-line blurbs may be new. Never trim or paraphrase while moving.
2. **Rollback ready** — git repo: `git mv`, one reviewable change. Otherwise snapshot
   first: `cp -a <skill_dir> /tmp/skill-snapshot-<name>` and verify against it.
3. **Zero dangling routes** — every route resolves, every subdocument reachable from
   SKILL.md, no orphans.

## Verification (not optional)

- `scripts/check_routes.py` — run `python3 <this-skill-dir>/scripts/check_routes.py "<skill_dir>"`: reachability,
  orphans, compass cap; add `--before <snapshot>` after a split for the conservation
  check. Deterministic, free, ALWAYS run after restructuring. Exit 0 clean / 1 issues.
- `scripts/eval_retrieval.py` — run `python3 <this-skill-dir>/scripts/eval_retrieval.py "<skill_dir>" --glm`
  (**--glm on by default**, user-approved standing policy 2026-06-10: per restructure,
  each subdocument is asked **3 times in parallel**, hit = majority vote ≥ 2/3 —
  absorbs single-call randomness. Total calls = 3 × subdocuments, one sweep, hard cap
  `--max-calls 90` on total, projected count printed before calling). All runs are
  foreground Bash calls, fully visible in the conversation; nothing runs in the
  background.
  **What it actually tests (self-referential, know the boundary):** the test query
  for each subdocument is its own `when-to-read:` line from the index — deterministic,
  not invented at test time. Level 1 scores keyword overlap (free); Level 2 asks
  glm-5.2 "Task: <when-to-read> → which file?". So it verifies *index
  distinctness* (can the router uniquely find the doc by its declared scenario), NOT
  real user phrasings. Badly written when-to-read lines usually FAIL (safe
  direction); the only false-green is a when-to-read that is unique yet disconnected
  from how the user actually asks. Therefore: **write every when-to-read as a real
  task sentence in the user's own words** — that makes the test queries match reality.
  **Grader duty (borrowed from skill-creator's grader): when reporting the hit-rate,
  also critique the test itself** — name any when-to-read line that is too generic,
  trivially distinct, or disconnected from real phrasings. A green run on weak queries
  is worse than useless; say so instead of presenting 100% as proof.
- Never declare a restructure done with a failing `check_routes.py`.

## Deliberately dropped from the old skill-structure

Deterministic text compression (`compress_doc.py`) — retired. Its lossless passes
saved almost nothing on real docs; wordiness is a semantic problem. Shorten by
meaning-level editing (LLM/human), guarded by the conservation rule when splitting.
