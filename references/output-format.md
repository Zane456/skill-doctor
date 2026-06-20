# Output Format — Layered Diagnosis Report

How Step 3 presents the diagnosis. Two facts drive the shape:

1. The reader owns the skill — they will edit it. But what they act on is not "which line is
   ugly", it is: **when this skill next runs, what does the LLM do wrong, and is fixing it safe?**
   file:line / field detail is the *evidence*, not the decision.
2. Output streams in a terminal — eyes land on the **bottom**. The audit trail sits in the
   middle (scrolled past); the actionable parts go last.

## Write the whole report in lesstoken style

Ultra-compressed. Drop filler (其实/就是/基本上/然后 · just/really/basically/actually),
pleasantries, hedging. Fragments OK. Short word over long. Arrows for causality (X → Y). One
word when one word enough. Pattern: `[thing] [action] [reason]. [next].` Aim: half the prose,
same facts.

Exact-keep — never compress, never translate: file:line, field / frontmatter-key / section
names, IDs (P0-1 …), code blocks, error strings, the failure-mode prefixes
(`[no-op]`/`[sediment]`/`[premature-completion]`/`[weak-leading-word]`/`[duplication]`/`[sprawl]`),
the `[skill-doctor]` status prefix.

Match the user's reply language — and commit to it, no half-mixing. When that language is
Chinese, the report is **basically all Chinese**: prose, section headers, AND the field labels in
the templates below all get translated. Don't strew English scaffolding through Chinese sentences.
Target mapping (use these, adapt as needed):

    verdict→结论 · before→修复前 · after→修复后 · risk→风险 · current→现状 · consequence→后果
    decision→解决方案 · fix→改法 · where→位置 · why→原因 · rec→建议 · blind spots→盲区 · passed→已通过

The only things that stay non-Chinese: the Exact-keep tokens above; **proper nouns** — the skill's
own name, role/tool names — keep their original form; and the language-neutral emoji (🟢/🟡/🔴 ·
✅/🤔/❌/⚠️). Everything else follows the reply language.

Auto-clarity exception (drop compression here): irreversible-fix warnings and any multi-step fix
sequence where fragment order could be misread — write those in normal prose. (Compression is
dropped for safety warnings and ordered sequences — clarity wins over brevity there.)

## Section order (top → bottom)

1. **Verdict** — one line: is the skill basically sound, which 1–2 buckets the problems fall in
   (trigger / body altitude / structure-routing / predictability).
2. **Quality scores** — the 4-dimension table (1–5) + a one-line **Passed** note + a one-line
   **Blind spots** note (what you could not check — unread reference, un-run script).
3. **Code layer** — the P0→P3 findings, the evidence. Header is exactly **Code layer** (or
   **代码层** in a Chinese report). Never drop it — it is why the verdict is trustworthy.
4. **✅ Safe to fix now** — pure fixes.
5. **🤔 Needs your decision** — judgment calls.
6. **Closing question** — one concrete action question. Last line = most visible.

## Quality scores — the 4 dimensions (1–5)

| dim | scores |
| --- | --- |
| Trigger/description | will it auto-fire on the right prompt, stay silent on the wrong one? |
| Body altitude | compass not manual — points to references, doesn't narrate them inline? |
| Structure & routing | references sorted right, every route resolves, ≤2-hop index? |
| Predictability | free of no-op / sediment / premature-completion / weak-leading-word? |

One line of **Passed** (what is already healthy) and one line of **Blind spots** (un-checked
surface) close this section. Honest blind spots > a clean-looking score.

## Code layer — severity, IDs, format

Findings sorted **P0 → P3** (definitions in `priority-tiers.md`), grouped under those headers.
Each gets a stable ID = `P<tier>-<n>` (P0-1, P1-2, P3-1 …) — the anchor the decision layer points
back to.

The fix-risk circle 🟢/🟡/🔴 goes **first**, then ID, the failure-mode prefix when one applies,
plain name, dimension; sub-lines below, lesstoken (facts kept, prose cut):

    🟢 P1-1 [sediment] Dead branch never reached — structure
    where: SKILL.md:42 (or the frontmatter key / reference filename)
    why:   <what the next LLM does wrong because of it — compressed>
    fix:   <concrete change>

Circles: 🟢 repair-only/additive (restores intended behavior, nothing working regresses) · 🟡
touches working logic (rewrites a live instruction, changes a trigger word) · 🔴 design/structure
change (splits the skill, deletes a rule/branch). P-tier ≠ risk circle — a P0 effect-break often
has a 🟢 fix.

Same violation in N places → **N separate findings**, each with its own line:field, so the user
can locate and fix each. Never merge them.

## Decision layer

Re-frame every finding into two buckets by **whether the user must decide anything**. Each item:
plain name + back-pointer **(Code layer: <ID>)**. Compressed.

**Altitude rule — this layer's reason to exist.** The Code layer already holds every line:field and
construct. This layer says *what the skill does wrong when it next runs, and what changes for the
user*. So:

- **No code artifacts here.** No line numbers, no filenames (`index.md`, `references/foo.md`), no
  constructs (frontmatter, `description:`, §X, "the third bullet"). All of that stays in the Code
  layer, reachable via (Code layer: <ID>). The moment you type a `.md` or a field name, you've
  fallen back to the code layer — rewrite the line.
- **Name a part by its job, not its file.** "the line that's supposed to make it auto-fire", "the
  step meant to print a confirmation" — never the file it lives in.
- **Speak run-time effect.** before/after/current = what happens *when the skill is invoked* — does
  it fire, does a step get silently skipped, does the LLM narrate instead of act. NOT "two sections
  disagree" — that mismatch is the *evidence* (Code layer). Here: what the mismatch *costs* — which
  prompt fails to trigger, which step quietly drops.

One worked rewrite — same finding, wrong altitude → right altitude:

    ✗ code-layer leak (what NOT to write here):
      current: description line 3 leads with "Helps you…" + missing the negative constraint, and
               §2.6 has no print line
    ✓ macro, split into mechanism + consequence (what TO write):
      current:     the skill relies on a weak opening phrase to get itself picked, and one of its
                   steps runs without announcing it
      consequence: on a matching prompt it often won't fire at all — and even when it does, that
                   silent step gets skipped and nobody is told

### Item layout — applies to every ✅ and 🤔 item
- **Number every item.** Prefix the title with an emoji digit, sequential within its bucket:
  1️⃣ 2️⃣ 3️⃣ … (past 🔟 use plain `11.`). Title bold, ID after it:
  `1️⃣ **<plain name>** (Code layer: <ID>)`.
- **Bold the label before every colon** — `**修复前**` / `**风险**` / `**现状**` / `**后果**` /
  `**解决方案**`, etc.
- **Align the colons.** Pad with full-width spaces (　) so all colons sit in one vertical column
  (uniform width = longest label `解决方案`, 4 CJK chars). **The padding goes OUTSIDE the bold** —
  `**风险**　　：`, never `**风险　　**：` (a full-width space right before a closing `**` makes the
  terminal render the `**` literally — bold breaks).
- **A choice never crams options behind `/`.** Break each option onto its own line, labeled
  `【方案 1】` / `【方案 2】` (English report: `【Option 1】` / `【Option 2】` — NOT emoji digits,
  those are the item numbering), indented under the label:

      **解决方案**：
      　【方案 1】 <option one, in effect terms>
      　【方案 2】 <option two>

### ✅ Safe to fix now
Pure fixes (🟢): something meant to work is broken/unwired; fixing only restores it, the skill's
logic is unchanged, nothing already-working regresses.

    1️⃣ **<plain name>** (Code layer: <ID>)
    **修复前**　：<bad thing the skill does when invoked now>
    **修复后**　：<right behavior once fixed>
    **风险**　　：低；only touches the already-broken path

### 🤔 Needs your decision
Judgment calls (🟡/🔴): a structure fork (split / restructure), a deletion, a trigger-word change,
or anything touching a path that currently runs.

    1️⃣ **<plain name>** (Code layer: <ID>)
    **现状**　　：<how the skill behaves now — the mechanism, by role not file>
    **后果**　　：<what that costs at run time — name a silent skip/mis-trigger when that's the risk>
    **解决方案**：
    　【方案 1】 <option one, in effect terms>
    　【方案 2】 <option two>
    **建议**　　：<your pick, what it touches, "won't change automatically">

### 现状 vs 后果 — keep them distinct
- **现状 (mechanism)** = how the skill is wired *right now*, named by role not file. No blame, just
  "this is the setup".
- **后果 (consequence)** = what that setup *costs* at run time. When the real risk is a silent skip
  (a step that drops with no error, a prompt that never triggers), name it here in one concrete
  sentence.

## Closing question
One line: offer to apply the ✅ Safe-to-fix items now (Step 4 still needs explicit "fix it"
confirmation per `apply-safety.md`), leave the 🤔 decision items.

## Mapping
- 🟢 → Safe to fix now　·　🟡 / 🔴 → Needs your decision
- P-tier (P0/P1/P2/P3) lives in the Code layer; the bucket lives in the decision layer.
  Independent — a P0 effect-break with a 🟢 fix is a "Safe to fix now" item.
