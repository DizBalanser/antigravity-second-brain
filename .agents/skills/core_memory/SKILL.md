---
name: core_memory
description: Dynamically update and evolve persistent long-term memory about user preferences, habits, rules, and life context.
---

# Core Memory Skill (Self-Evolving Dossier)

## Architecture
Inspired by stateful memory systems (like Letta / MemGPT), this skill allows the AI to autonomously maintain and evolve its own core beliefs and knowledge about the user, without needing Docker, external SQL databases, or heavy infra.

All memory lives in standard markdown files:
- `_context/PROFILE.md` — Core identity, long-term goals, habits, values, communication preferences.
- `_context/RULES.md` — Hard boundaries and interaction rules.
- `_pool/todo.md` & `_pool/ideas.md` — Working memory and ideas buffer.

## When to Update Memory
Trigger automatic memory updates when:
1. User states a persistent preference (e.g., "I don't eat after 8 PM", "I prefer concise bullet points").
2. User makes a major life decision, pivots projects, or shifts goals.
3. User corrects the AI on an assumption.

## How to Mutate Memory
1. Check `_context/PROFILE.md`.
2. Locate or create the section `## 🧠 Core Memory & Evolving Facts`.
3. Append a dated bullet point:
   `- [YYYY-MM-DD] **<Category>:** <Detail>`
4. Confirm to the user: "Updated your core memory dossier. I will remember this across all future sessions."
