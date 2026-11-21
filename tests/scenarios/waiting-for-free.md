# Scenario: waiting-for-free

Prompt: `waiting-for-free.prompt.md`.
Passes when: one waiter that exits when CI finishes (or `gh pr merge --auto`); no sleep-and-check turns; no
`pgrep -f` self-match; no stale-log false start; doesn't end its turn trusting a notice.

## Without
- Good: `gh pr checks 42 --watch` in the background; byte offset into `queue.log`; `pgrep -f '[m]ergequeue…'`.
- Ends the turn on both tasks and relies on the exit notification to wake it ("Then I end my turn").
- Doesn't consider `gh pr merge --auto` (no wait at all).
- Contaminated run (rules in context) for reference: still wrote `until … || ! pgrep -f 'mergequeue.sh 40 41'`,
  the self-match trap.

## With
- Pass. `gh pr merge 42 --auto --squash` first; fallback one background `gh pr checks --watch && merge && echo DONE`.
- Task 2: PID via `[m]` pattern, then `while kill -0 $PID`; log offset; fresh `queue43.log`; won't start 43 if the
  other run died. Names both traps explicitly.
- As a lead it still ends the turn on a background command (allowed by the skill); adds a Monitor until-loop if the
  notice doesn't arrive.
