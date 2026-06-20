# SKILL.md Body Size and Splitting

The SKILL.md main file is a "compass", not a "manual". The shorter the body, the sharper it is.

## Hard limit: < 500 lines

Anthropic officially requires the SKILL.md body to be **< 500 lines**. Exceeding it significantly hurts Claude's execution precision — under long-context pressure, Claude skips details and takes shortcuts.

Community consensus is more aggressive: **body < 200 lines** is usually more reliable.

## Splitting decision: when to move content to references/

Split by content nature, not by "it looks too long":

| Content nature | Where it goes |
|----------------|---------------|
| Trigger conditions, the 4-5 step main workflow, hard-rules quick reference | **SKILL.md body** (compass) |
| Detailed standards / checklists / anti-pattern libraries | `references/<topic>.md` |
| Concrete variants of a thing (e.g. different languages/frameworks) | `references/<variant>.md` (one per variant) |
| Full API docs / long schemas / datasets | `references/<name>.md` |
| Executable scripts | `scripts/<name>.<ext>` |
| Templates, boilerplate, fonts, images | `assets/<name>` |

## Anti-patterns

### ❌ Putting "When to Use This Skill" in the body
Trigger conditions are **only effective in the description** — the body is read only after triggering, so writing "when to use" there is dead code.

### ❌ Piling dozens of anti-examples in the body
1-2 anti-examples are enough to build intuition. Move the rest to `references/anti-patterns.md`, read on demand.

### ❌ Nested references (references citing references)
Anthropic found in testing: when nested, Claude peeks with `head -100` and **leaves after reading only half**.
**References must be only 1 level deep** — every references file is linked directly from SKILL.md.

### ❌ Copying the workflow summary into the description
If the description summarizes the workflow, Claude reads the description, takes a shortcut, and skips the body.
The description should only say "when to use + what expert it is", the workflow goes in the body.

### ❌ Writing "see references/foo.md for more" in the body without saying **when** to read it
State the condition explicitly:
```
✅ "If body > 500 lines, read references/body-quality-checklist.md"
❌ "See references/body-quality-checklist.md for more details"
```

## Self-check before splitting (skill-doctor uses this list)

When diagnosing a body, ask in order:

1. Body line count > 500? → **must fix**, pick the longest section to split out
2. Body line count > 200? → suggest splitting, see the section scan below
3. Section scan: look for these signals
   - A section > 80 lines → split-out candidate
   - 5+ repeated anti-examples → move anti-examples to references
   - Multi-step detailed operations (each step > 20 lines) → move to `references/workflow-<name>.md`
   - Detailed API/schema → move to references
4. Each references file > 100 lines? → add a table of contents at the top of the file (for Claude's peeking)

## Standards for the reference files themselves

- **Descriptive file names**: `description-templates.md` ✅; `docs2.md` ❌
- **Forward-slash paths**: cross-platform compatible (Windows backslashes break)
- **Table of contents at the top** (if > 100 lines): so even if Claude peeks, it knows the whole picture
- **Do not repeat content already in SKILL.md**: information lives in exactly one place
