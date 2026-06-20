# Language: default to English

A SKILL.md body and its references default to English — it is the most reliable language for LLM instruction-following. Use Chinese (or any other non-English language) only when there is a concrete reason:

- Trigger keywords in the `description` that the user actually types in that language (e.g. a bilingual user) — keep these.
- Domain content that is inherently in that language (sample text, fixed terms, quoted material).

When auditing, flag unnecessary non-English content in the body or references as ⚠️ and recommend translating it to English. Do not flag the two justified cases above.
