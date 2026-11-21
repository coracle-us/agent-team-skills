---
name: waiting-for-free
description: Use when a build, CI run, deploy, test suite or long script will take more than a minute or two, or when one job must start only after another finishes.
---

# Waiting for free

**Waiting should cost nothing.** A model turn re-reads the whole context, so every "is it done yet?" check is a full
turn. And a big context left idle past the prompt-cache lifetime (5 minutes by default) is written to the cache again,
in full, on the next turn.

Why: in a 12-day agent-team build, 3,019 sleep-and-check loops and 1,039 cache rebuilds after idle gaps; the rebuilds
alone were roughly 30–40% of all cost.

## Pick the cheapest wait

1. **No wait at all.** Let the platform do it: `gh pr merge 42 --auto --squash` merges when the *required* checks
   pass, with zero tokens spent. It needs auto-merge allowed and required checks in branch protection; without
   them it errors or merges at once.
2. **One waiter that exits when the job does**, run in the background so you're woken once:
   `gh pr checks 42 --watch` (Bash `run_in_background`), or wait on a process id: `while kill -0 $PID; do sleep 15; done`.
   Sleeping inside a background command is free; it isn't a model turn.
3. **A big context and a long wait?** Write a handoff note and end, and let a small fresh agent or a script do the
   step after the wait.

## Rules

- Long scripts end with a `DONE` or `FAILED` line and touch a marker file. `rm -f job.done` before starting the job,
  or a leftover marker fires at once.
- **Subagents never end their turn waiting.** Ending the turn hands back to the lead, and the job's notice may never
  wake you. Keep working, or block on a Monitor until-loop: `until [ -f job.done ]; do sleep 10; done`.
- The lead never ends a turn "waiting for X" unless X is a person or a background command that will wake it.

## The three waiter traps

| Trap | Why it bites | Fix |
|---|---|---|
| `pgrep -f "mergequeue.sh 40"` in a wait loop | Matches the wait loop's own command line, so the loop never ends | Wait on a PID with `kill -0`, or use `pgrep -f '[m]ergequeue.sh 40'` |
| `grep -q 'ALL MERGED' queue.log` on a log that's appended to | Fires at once on the *previous* run's line; two runs then collide in one checkout | A fresh output file per run, or read only bytes after a saved offset (`tail -c +$((off+1))`) |
| Ending the turn and trusting the completion notice | Notices don't always wake an idle agent; agents stalled 30–60 minutes this way | Block on a done marker with Monitor, or keep working and check it before you stop |

Queue chained jobs in **one** call (`mergequeue.sh 40 41 43`) instead of chaining waiters.
