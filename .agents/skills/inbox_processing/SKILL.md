---
name: inbox_processing
description: Process raw captures, notes, voice transcriptions, and links from 00_Inbox into P.A.R.A. folders.
---

# Inbox Processing Skill

## When to Use
Activate when the user asks to "process inbox", "sort my captures", or during periodic review.

## P.A.R.A. Routing Rules
1. Inspect files in `00_Inbox/`:
   - Has a deadline or definitive end goal? -> Move to `10_Projects/<Project_Name>/`
   - Long-term ongoing responsibility (health, finance, career, home)? -> Move to `20_Areas/<Area_Name>/`
   - Reference material, book summaries, cheatsheets, tools? -> Move to `30_Resources/<Topic>/`
   - Inactive, completed, or deprecated? -> Move to `40_Archive/`
   - Standalone actionable to-do? -> Append to `_pool/todo.md`
   - Raw spark / idea for future consideration? -> Append to `_pool/ideas.md`
2. Frontmatter & Linking:
   - Ensure every note has YAML frontmatter with `summary:` and `tags:`.
   - Add at least 2 relevant `[[wiki-links]]` to interconnect notes across the Obsidian graph.
3. Cleanup:
   - Remove or archive the raw inbox note once sorted.
