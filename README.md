# agent-team-skills

**In agentic coding you pay for agents to remember, not to work.**

In October 2026 I used 25.5 billion tokens through Claude Code, most of it leading teams of agents that built a multiplayer
browser game in 12 days. Only **0.24%** of those tokens were the model writing anything: code, prose, commands.
**96.4%** was the model re-reading context it already had, from the cache, on every single call.

So I audited every transcript to find where the re-reading went, and turned what I found into seven Claude Code
skills. Each one fires at the moment the leak happens, for whoever is **leading a team of agents**.

## Install

In Claude Code:

```text
/plugin install agent-team-skills --marketplace coracle-us/agent-team-skills
```

On older versions, two steps:

```text
/plugin marketplace add coracle-us/agent-team-skills
/plugin install agent-team-skills@agent-team-skills
```

Then check your own week: ask Claude "where did my tokens go this week?" and the `audit-your-spend` skill runs.

## What I found, and the skill for each

From the 12-day build (Oct 18–30: 21.9B tokens, 292 agents plus 2 lead sessions), as `audit-your-spend` counts it. Cost shares are estimates from API
list-price ratios.

| Skill | Fires when | The leak it stops |
|---|---|---|
| `briefing-agents` | you're about to spawn an agent | Agents were **86%** of tokens. One agent kept alive for **117 hours** made 1,320 calls at ~500k context each: **12%** of all cost by itself. |
| `waiting-for-free` | a build, CI run or deploy will take minutes | over **2,000** sleep-and-check loops, and **1,154** cache rebuilds after idle gaps: about **35%** of all cost. |
| `context-hygiene` | a session is getting heavy, or CLAUDE.md is growing | Calls carrying over 400k context were **46%** of calls and **70%** of cost. CLAUDE.md grew from 10 KB to 255 KB, and a new agent's starting context went from **32k to 113k** tokens. |
| `looking-cheaply` | you're about to take screenshots | More than **6,500** screenshots, each re-read on every later turn. |
| `merging-in-batches` | you're merging a stack of PRs, or a test is flaky | One CI run for a resolved stack, not one per PR; a flaky test gets one logged retry, not a restart. |
| `rulings-become-tests` | the lead makes a call that must keep holding | Fresh agents don't know yesterday's decisions. A test does. |
| `audit-your-spend` | you ask where the tokens went | Runs locally on your own logs and shows all of the above for your week. |

### `briefing-agents`

Agents are disposable: one job, one result, then the agent ends. The skill gives the shape of a brief (goal, where to
look, what's ruled out, done when) and a footer to paste into every brief: stop your servers, never end a turn
waiting on a job, no sleep loops, state goes in files.

### `waiting-for-free`

Waiting should cost nothing. Let the platform wait (`gh pr merge --auto`), or run one background waiter that wakes the
agent once. Includes the three waiter traps that bit us: `pgrep -f` matching its own wait loop, a "done" grep firing
on the previous run's log line, and completion notices that don't wake an idle agent.

### `context-hygiene`

You pay for the window you carry, not the window you have. Near 250k tokens, write a handoff file and start fresh.
Keep CLAUDE.md an index under about 20 KB; detail goes in docs agents read only when their task touches it.

### `looking-cheaply`

Capture everything, pixel-diff against the last run, view one labelled contact sheet, and zoom only where something
changed. Or hand the looking to a short-lived reviewer that reports in words.

### `merging-in-batches`

Run the slow check once on the tip of a resolved stack, not once per PR. A flaky test gets one logged retry; two
failures stop the queue; then fix the root (pin the clock and the seed).

### `rulings-become-tests`

When the lead says "note that" about a rule, write the guard test in the same turn, with the ruling quoted in its
failure message, and one line in CLAUDE.md pointing at it.

### `audit-your-spend`

A standard-library Python script that reads `~/.claude/projects` and prints counts and percentages: tokens by day and
week, the mix, heavy calls, cache rebuilds, the costliest sessions and how long they lived, starting context by day,
polls and images. It's read-only, makes no network calls, and never prints message text, project names or prices.
Run it directly from a clone of this repo:

```bash
python3 skills/audit-your-spend/scripts/audit.py --since 2026-11-01 --until 2026-11-07
```

## How the skills were tested

Each behaviour skill has a scenario in `tests/scenarios/`: a fresh agent answers it once without the skill and once
with it (`zsh tests/run-scenarios.sh <out-dir> [skills-root]`). Without the skills, a fresh agent views all 12 screenshots
at full size, keeps working at 300k context ("300k of 1M is not a problem"), and runs CI five times on a stack it
could check once. With them, it doesn't. The audit script and the repo have unit tests
(`python3 -m unittest discover -s tests`), and on my own logs the audit reproduces my October total to the token.

## Licence

MIT. By Jon McBee, [Coracle](https://github.com/coracle-us).
