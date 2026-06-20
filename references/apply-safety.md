# Apply-safety: size gate, pre-deletion check, close the loop

Detailed procedure for SKILL.md **Step 4** (apply fixes with Edit, after user confirmation). The body keeps "never Edit without confirmation" and the `Applied` print line; the rest is here.

**Size gate**: before acting, compute the post-fix body line count from the line delta of the Edit `new_string`. If `new_lines > old_lines × 1.3` (growth >30%), print a warning and ask the user whether they accept it — most likely some content should move into `references/` rather than be stuffed into the body.

**Pre-deletion check**: for deletions of **rules / trigger branches / applicability conditions / workflow steps** (excluding pure formatting, wording, dedup), judge in the following order, to prevent deleting general paths just to pass the dry-run:
1. List **at least 2** reasonable prompts, beyond the dry-run prompt, that would still hit this content → can list them: deletion forbidden, instead merge or split into condition branches.
2. Can list only 1 → show that prompt to the user and ask: "Are there other reasonable prompts that would hit this branch?" User supplies a 2nd → back to deletion forbidden; user confirms there are none → deletion allowed, Step 4 print line appends `narrowed (1 prompt found): <content>`.
3. Can list none → mark as a dead branch, deletion allowed, Step 4 print line appends `dead-branch removed (0 prompts found): <content>` for traceability.

**Close the loop**: if the fix touched the description or restructured references/, end with the handoff line — `[skill-doctor] Verify: restart session, then re-run Step 2.6 (description must appear, not name-only) / re-run check_routes.py` — an in-session pass proves nothing for either, since the listing only refreshes on session start.
