# Mechanical Pitfalls of YAML / Frontmatter

These are **purely mechanical, must-fix** hard rules — violating them causes problems, usually with no error message at all.

## 1. A multi-line description gets broken by auto-formatting

```yaml
# ❌ folded block (>) and literal block (|) are prone to failure
description: >
  SKILL.md quality expert. ALWAYS invoke this skill when editing
  any SKILL.md file. Do not modify SKILL.md directly.

# ❌ Prettier / auto-formatters "reflow" the above into a single line then fold it back, losing characters or breaking indentation
```

Fix:

```yaml
# ✅ single logical line + .prettierignore configuration
description: SKILL.md quality expert. ALWAYS invoke this skill when editing any SKILL.md file. Do not modify SKILL.md directly. Use this skill first.
```

💡 Configure your project formatting tool (like Prettier) to ignore skill files. Add this to your `.prettierignore` file in the project root:
```
**/*SKILL.md
```


If it is too long and you must wrap, YAML's "flow scalar" auto-joins line breaks (replacing them with a space), but **there can be no blank line**:

```yaml
description: SKILL.md quality expert. ALWAYS invoke this skill when
  editing or writing any SKILL.md file. Do not modify SKILL.md
  directly without consulting this skill first. Use this skill first.
```

The line break after each line becomes a space, so it reads like one long sentence. **Avoid blank lines** — a blank line is interpreted as a "paragraph separator" and the behavior is unpredictable.

## 2. Silent truncation of the character budget

Single source of truth: `description-templates.md` §"The character budget" (per-description 1024 portable / 1536 CC ≥ 2.1.105; whole listing ≈ 1% of context; levers and target bands there). Measure with `scripts/check_listing_budget.py` — do not quote numbers from memory.

## 3. The name field regex

Only allowed: **lowercase letters + digits + hyphens**. Everything else errors out or is silently rejected.

```yaml
# ❌
name: Skill Doctor       # uppercase + space
name: skill_doctor       # underscore
name: skill-doctor!      # special character
name: skill.doctor       # dot

# ✅
name: skill-doctor
name: writing-skills
name: scheduled-task-macos
```

## 4. Third person is mandatory

The description is injected into the system prompt; first/second person breaks the discovery mechanism:

```yaml
# ❌
description: I help you write better SKILL.md files
description: You can use this skill to review SKILL.md files

# ✅
description: SKILL.md quality expert. ALWAYS invoke this skill when...
```

## 5. Frontmatter field scope

Required: **`name`** and **`description`**. Recognized optional fields:

- `allowed-tools` — restrict the tools this skill may use. **Audit it**: if the body instructs tool X (e.g. Bash for scripts) but `allowed-tools` omits X, the skill breaks at runtime — flag as P1.
- `disable-model-invocation: true` — forbid automatic triggering (for skills with strong side effects, e.g. deploy)
- `argument-hint`, `model` — supported by Claude Code for invocation hints / model override

Informational fields like `metadata:` and `license:` are tolerated and ignored by Claude Code — **do not flag them** (empirically: 19/13 installed skills carry them and load fine). Flag a field only when it breaks YAML parsing or shadows a recognized field with the wrong type.

## 6. Use forward slashes for file paths

```markdown
✅ scripts/helper.py
✅ references/templates.md

❌ scripts\helper.py     # Windows backslash blows up on Unix
❌ references\guide.md
```

## 7. Syntax for referencing other files

```markdown
✅ See [body-quality-checklist.md](body-quality-checklist.md)

❌ See @body-quality-checklist.md
   # the @ syntax forces an immediate load, eating a large amount of context
```

The `@` prefix is a force-load — it makes Claude read the file into context immediately, bypassing progressive disclosure.

## Diagnostic checklist (skill-doctor checks against this)

Mechanical check — one wrong item is a "must fix":

- [ ] Is the description a single logical line (no blank line / no `>` `|` block)?
- [ ] Within the caps and bands? (numbers live in `description-templates.md` §budget; measure via `scripts/check_listing_budget.py`)
- [ ] Is the name `^[a-z0-9-]+$` **and** equal to the directory name?
- [ ] Is the description third person (no "I"/"you" subject)?
- [ ] Frontmatter fields all recognized or informational (see §5)? If `allowed-tools` present, does it cover every tool the body instructs?
- [ ] Do all paths use `/`, not `\`?
- [ ] Do references citations use `[name](path)`, not `@path`?
- [ ] Is the project configured with `.prettierignore` to protect SKILL.md files from auto-formatting?

