---
name: daily_planning
description: Generate a structured daily plan based on user priorities, active projects, schedule, and energy levels.
---

# Daily Planning Skill

## When to Use
Activate when the user asks for a daily plan, morning kickoff, or "what should I focus on today?"

## Workflow
1. Read Context:
   - `_context/PROFILE.md` — goals, core habits, operating context.
   - `_context/FOCUS_SYSTEM.md` — daily structure and rules.
   - `_pool/todo.md` — active pending tasks.
   - `_daily/` — yesterday's daily file to see what was closed vs deferred.
2. Filter for Maximum Leverage:
   - Rule of 3: Select NO MORE THAN 3 non-negotiable priority tasks.
   - Categorize by Deep Work block (morning high cognitive load) vs Shallow Work (admin, emails, routine).
3. Generate Today's File:
   - Write to `_daily/YYYY-MM-DD.md` with YAML frontmatter.
   - Include sections: Top Priorities, Schedule / Time Blocks, Capture Chronicle, Evening Shutdown.
4. Keep Momentum:
   - Challenge the user with: "Which of these top 3 are you tackling right now?"
