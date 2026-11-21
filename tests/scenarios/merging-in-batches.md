# Scenario: merging-in-batches

Prompt: `merging-in-batches.prompt.md`.
Passes when: CI once at the stack's tip; queued in one call; flaky test retried once and logged; root fix proposed
(pinned clock or seed).

## Without
- Starts CI on all five PRs in parallel, then merges bottom-up with a rebase, force-push and fresh 40-minute CI per
  PR ("about 3.5 hours"). Merging #55 alone is a shortcut to ask about, not the plan.
- Flake handling good: read the failure, re-run once, measure the rate, time-boxed root-cause hunt, no skipping.

## With
- Pass. Checks repo rules first and asks before squash/rebase; CI once on #55; merge commit; closes non-main-target
  PRs with a link; one-call queue. Flake: read, retry once, log in an issue, two failures stop, root fix (pin clock and
  seed) in its own PR. "About two CI runs, roughly 80 minutes, instead of five."
