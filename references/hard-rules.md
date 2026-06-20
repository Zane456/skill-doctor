# Hard rules quick reference (a violation is an error, not a suggestion)

| Rule | Source |
|------|--------|
| description ≤ 1024 chars (portable spec; Claude Code ≥ 2.1.105 accepts 1536) | Anthropic spec / CC v2.1.105 release notes |
| listing-budget overflow (shared pool ≈ 1% of context; overflow = silent name-only truncation, auto-trigger dies) is always **reported** — population-level fact; remedied only by a user-initiated global pass, never by editing the audited skill | CC issues #56710 / #47627 |
| description in third person | Anthropic best-practices |
| name uses only lowercase letters + digits + hyphens | Anthropic spec |
| body < 500 lines | Anthropic / community consensus |
| routing depth ≤ 2 hops (SKILL.md → index.md → file); nested indexes forbidden — the third hop is where LLM recall dies | structure-surgery.md (hardened from practice) |
| zero dangling routes / zero orphan subdocuments (verify with `scripts/check_routes.py`) | structure-surgery.md iron rule 3 |
| YAML description on a single logical line (no `>` `|`) | Prettier reflow will break it |
| every step of a multi-step workflow must produce visible output | Seleznov's second problem |
| prefer `references/` `scripts/` `assets/`; custom dirs (`agents/`, `evals/`) also allowed | agentskills.io spec (`...` = any additional files/dirs) |
| a skill's claim about its **own** performance/validation (verified / tested / "N% accurate" / "N iterations") must point to in-repo evidence (`evals/` or `reports/`) or be cut/softened; plain functional descriptions (creates / measures / optimizes X) are exempt — the anchor is *asserting the skill's own validated status*, not the presence of a performance word | evidence-gating (best-practices) |
