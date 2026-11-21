# Scenario: briefing-agents

Prompt: `briefing-agents.prompt.md`. Runner: `zsh tests/run-scenarios.sh <out> [skills]` (sonnet, headless, empty folder).
Passes when: the brief is narrow (goal, files, ruled out, no pasted stack or history), one job then stop, stop servers
before reporting, never end a turn waiting on a job; ends with the footer; follow-ups go to a fresh agent.

## Without
- Disposable already ("returns its report and is done"); fresh briefs for the pricing page and queries.
- Re-pastes the stack (ORM, auth, Stripe, CI); ~470-word brief.
- "Check the PR's CI result with `gh pr checks` before reporting done": the agent waits on a 14-minute CI, with no
  word on how to wait.
- Never says to stop dev servers or background processes.
- "I'd only message it again if review or CI feedback needs a follow-up fix": the agent stays alive.

## With
- Pass. Four-part brief (goal, where to look, ruled out, done when) plus the footer verbatim; no stack paste (~200
  words of brief). The agent ends after the PR; review fixes and follow-ups get fresh agents; offers `gh pr merge --auto`
  instead of having the agent sit through CI.
