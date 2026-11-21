---
name: briefing-agents
description: Use when about to spawn a subagent or teammate, writing an agent's brief or prompt, or deciding whether to keep an agent around for more work.
---

# Briefing agents

**Agents are disposable.** One job, one result (a PR or a report), then the agent ends. State lives in files and PRs,
never in a long-running context. Every turn an agent takes re-reads its whole context, so an agent kept alive across
jobs pays again and again for history it no longer needs.

Why: in a 12-day build with 292 agents, agents were 86% of all tokens. One agent kept alive for 117 hours to run a
merge queue made 1,320 calls at about 500k tokens of context each: 15% of all cost, by itself.

## The brief

A brief has exactly these parts, in this order. Nothing else.

1. **Goal**: one sentence, one deliverable.
2. **Where to look**: the files or the failing command. Not the stack, not the project's history: the agent can read
   the repo, and every word you paste is re-read on every one of its turns.
3. **Ruled out**: what you already know isn't the cause, and what not to touch.
4. **Done when**: the check that proves it (a test passing, a PR open).
5. **The footer**, pasted as is:

```text
Working rules:
- One job. When it's done, report in under 150 words and stop. Don't take on follow-up work.
- Stop every dev server, watcher and background process you started before you report.
- Never end your turn "waiting for" a job: ending your turn hands back. For anything over ~10 minutes,
  run it in the background and keep working, or block on a watcher that exits when the job is done.
- No sleep-and-check loops. If you push a PR, don't wait on CI unless the brief says to.
- Put anything worth keeping in a file or the PR description, not in your report.
```

## After the result

The agent ends. Review changes, the next job, and follow-ups get a **fresh** agent whose brief points at the PR. Don't
"message the same agent while it's still alive": that is how a 10-minute agent becomes a 117-hour one.

Prefer doing a small thing yourself over spawning. Prefer fewer, smaller agents over many large parallel ones.

## Common mistakes

| Mistake | Instead |
|---|---|
| Pasting the stack or a project summary "for context" | Point at the files; the agent reads what it needs |
| "Check CI before reporting done" | Report with the PR open; the lead handles CI (see waiting-for-free) |
| Keeping the agent for the next task because it "knows the code" | It knows 500k tokens of the old task. Start fresh |
