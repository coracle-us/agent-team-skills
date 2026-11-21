---
name: merging-in-batches
description: Use when merging several PRs at once, a stack of dependent PRs, a merge queue, or when a CI test fails intermittently and blocks merges.
---

# Merging in batches

**Run the slow check once for the combined result, not once per PR.** CI is the slowest step an agent team has; every
extra run is calendar time and another wait.

## A stack that's already resolved

If PRs #51…#55 are stacked and #55's branch contains all of them:

1. Retarget #55 to main if it's based on #54's branch (`gh pr edit 55 --base main`); CI that only runs for PRs
   into main starts then. Run CI **once**, on #55. Don't start CI on #51–#54; their code is a subset of #55's.
2. When it's green, merge #55 into main with a **merge commit** (or fast-forward), so the commits of #51–#54 land
   too. PRs that target main are then marked merged on their own; any that target another PR's branch, close with
   a comment linking #55.
3. If the repo requires squash merges, or a review per PR, ask the owner before step 2. Don't rebase and re-run CI
   five times without asking: at 40 minutes a run, that's most of a day.

Queue PRs in **one** call (`mergequeue.sh 51 52 53`), never as chained waiters (see waiting-for-free).

## A flaky test

1. Read the failure first: is it the known flaky test, failing the known way?
2. If yes, re-run that test or job **once**, and log both runs (run ids, error) in an issue.
3. Two failures stop the queue: it's real until shown otherwise.
4. Then fix the root, in its own small PR. Time and randomness cause most flakes: pin the clock and the seed in tests.
5. Never skip the test, loosen its assertions, or raise global retries to get green.

Why: an unexplained flake restarts the slowest check you have. One logged retry keeps the queue moving without
hiding a real failure, and pinning the clock and seed removes the cause.
