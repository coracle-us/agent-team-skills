---
name: audit-your-spend
description: Use when asked where Claude Code tokens went, why usage or cost is high, how much an agent team used this week, or to check a week of sessions for leaks.
---

# Audit your spend

**In agentic coding you pay for agents to remember, not to work.** Output is usually under 1% of tokens; the rest is
context re-read on every call. This audit shows where that re-reading went on this machine.

## Run it

```bash
python3 <this skill's base directory>/scripts/audit.py                    # last 7 UTC days
python3 <this skill's base directory>/scripts/audit.py --since 2026-10-01 --until 2026-10-31
```

`--json` gives the same report as data; `--root` points at another copy of `~/.claude/projects`. It is read-only,
standard-library Python, makes no network calls, and prints counts and percentages only: no message text, no project
names, no prices. Agent names are shown as short hashes.

## Read it back

Lead with the one number that surprises: the output share ("only 0.2% of tokens were the model writing anything").
Then name each leak the report shows, biggest first, with the skill that fixes it:

| Report line | What it means | Fix |
|---|---|---|
| Cache rebuilds after idle gaps | A big context sat idle past the cache lifetime, then paid to be written again | `waiting-for-free` |
| Sleep-and-check polls | Each check is a full turn over the full context | `waiting-for-free` |
| Heavy calls (over 400k) | Long sessions carrying everything they ever read | `context-hygiene` |
| Starting context rising day by day | The briefing file (CLAUDE.md) is growing | `context-hygiene` |
| Costliest sessions, long-lived | An agent kept alive across many jobs | `briefing-agents` |
| Images in context | Every screenshot is re-read on every later turn | `looking-cheaply` |

Cost shares are estimates from API list-price ratios; say so. If the data starts later than the window asked for,
Claude Code has already deleted older transcripts (`cleanupPeriodDays`, default 30): say that the total is short, not
that usage was low.

## Common mistakes

- Pasting the report somewhere public without asking. It is the user's own usage; it's theirs to share.
- Quoting dollar amounts. The report has none on purpose; percentages are the honest unit across plans.
- Treating one bad day as a trend. Read the by-week lines before judging.
