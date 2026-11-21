---
name: context-hygiene
description: Use when a session's context is past about 200k tokens, a session has run for days, or when adding to CLAUDE.md or another file every agent reads.
---

# Context hygiene

**You pay for the window you carry, not the window you have.** Every call re-reads the whole context. A 1M window
doesn't make 300k cheap: it makes it possible, so nothing forces a restart.

Why: in a 12-day agent-team build, calls carrying over 400k tokens of context were 46% of calls and 70% of all cost.

## Restart at about 250k

When a session nears 250k, or the next task has nothing to do with the last one:

1. Write a handoff file: what's in flight (PRs, branches, CI state), decisions made and why, what's waiting on the
   user, and the first thing to do next.
2. Stop any servers and watchers you started.
3. Tell the user: "This session is heavy; start a fresh one that reads `<handoff file>`." Then stop.

Don't start new work in the heavy session, even by dispatching agents from it: every dispatch and every report is
another turn over the full context.

| Thought | Reality |
|---|---|
| "300k of 1M is fine" | It's 300k re-read on every turn from now on |
| "I know the codebase now; a fresh session would lose that" | What matters goes in the handoff file. The rest is stale |
| "I'll compact later" | Every turn until then costs the full context |

## The briefing file is an index

Everything in CLAUDE.md is read by every agent before it does anything, and carried on every turn after.

- Keep CLAUDE.md under about 20 KB: rules, settled decisions, conventions, and an index.
- Feature detail goes in its own doc (`docs/<topic>.md`, or one row in a features doc). CLAUDE.md gets **one line**
  pointing at it.
- A rule that truly every agent needs stays in CLAUDE.md, as one sentence.
- If CLAUDE.md is already over 20 KB, say so and offer to split it.

Why: in that same build, CLAUDE.md grew from 10 KB to 255 KB, and a new agent's median starting context went from 32k
to 113k tokens before it had done anything.
