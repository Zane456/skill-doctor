# assets/ vs references/ vs scripts/ — official spec definitions

Source: agentskills.io/specification

## Directory structure

```
skill-name/
├── SKILL.md       # Required: metadata + instructions
├── scripts/       # Optional: executable code
├── references/    # Optional: documentation
├── assets/        # Optional: templates, resources
└── ...            # Any additional files or directories
```

The trailing `...` means **custom directory names are allowed**.

## Official definitions of the three standard directories

### `scripts/`

Contains executable code that agents can run. Scripts should:
- Be self-contained or clearly document dependencies
- Include helpful error messages
- Handle edge cases gracefully

Supported languages depend on the agent implementation. Common options include Python, Bash, and JavaScript.

### `references/`

Contains additional documentation that agents can read when needed:
- Detailed technical reference
- Form templates or structured data formats
- Domain-specific files

Keep individual reference files focused. Agents load these on demand, so smaller files mean less use of context.

### `assets/`

Contains static resources:
- Templates (document templates, configuration templates)
- Images (diagrams, examples)
- Data files (lookup tables, schemas)
