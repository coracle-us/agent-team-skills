# agent-team-skills: design

Date: 2026-11-20. Author: Jon McBee (Coracle), with Claude.

## Intent

In October 2026 Jon ran teams of Claude Code agents in parallel to build a multiplayer browser game, and used
25.5 billion tokens doing it. An audit of the transcripts showed where the tokens went: almost all of it was agents
re-reading context they already had, not doing work. **You pay for agents to remember, not to work.** The lessons from
that audit currently live in one private repo's notes. This project packages them as Claude Code skills in a public
repo, so any lead running a team of agents can install them, and announces them in a LinkedIn post whose job is to
get people to install them.

## Who it's for

Someone **leading a team of Claude Code agents**: spawning agents in parallel, waiting on CI, merging a stream of PRs,
coming back to sessions over days. (Jon's words: "for someone leading a team of claude code agents like i did".) Not
for a solo developer with one session; they don't hit these leaks.

## Goals

- Seven skills, each firing at the moment a leak happens, not as general advice.
- One-command install as a Claude Code plugin from a public GitHub repo under **coracle-us** (Jon's choice).
- Each skill shows its value the first time it fires (e.g. the brief skill prints a footer ready to paste into an
  agent's brief; the audit skill prints the reader's own leak report).
- A LinkedIn post (Jon posts it himself) that ends in the install commands.

## Non-goals

- A general collection of Claude Code tips.
- Hooks or automation that enforce the rules (possible later).
- A public copy of the original audit page.

## Anti-goals (a failure even if it works)

- **Anything that identifies the original project or employer**: no company, project, game or coworker names,
  no internal paths, script names, URLs or repo names. "A multiplayer browser game, built in 12 days" is the
  most specific it gets.
- **Dollar figures anywhere** (Jon's ruling). Tokens, counts and percentages only. Percentages of cost are fine.
- **Claims the numbers don't back.** The earlier "a third to half was avoidable" is an estimate: leave it out, or say
  plainly that it's an estimate.
- **Skills that themselves bloat context.** Short SKILL.md files, precise descriptions so each loads only when its
  moment comes.

## The numbers (all measured; use only these)

October 2026, all of Jon's Claude Code use (from session logs, each API response counted once by message id +
request id):
- 25.5B tokens (25,461,485,789). Output was 0.10%. Cache reads 96.5%, cache writes 3.4%.
- Busiest week: 15.5B tokens (Oct 19–25).

The 12-day audit of the game build (Oct 18–30, 23.0B tokens, 292 agents plus 2 lead sessions):
- Agents were 86% of tokens and 93% of cost.
- Output (everything Claude actually wrote) was 0.2% of tokens.
- Cache rebuilds after idle gaps: 1,039 of them, 583M tokens, roughly 30–40% of cost. An agent waits 5–60 min
  (for a build, a test run or the human), the cache expires, and the next turn writes its whole context again.
- One merge-queue agent kept alive 117 hours: 1,320 calls at about 500k context each, 15% of all cost.
- Calls carrying over 400k tokens of context: 44% of calls, 71% of cost.
- The project briefing (CLAUDE.md) grew from 10 KB to 255 KB; a new agent's median starting context went from 32k
  to 113k tokens.
- 6,574 screenshots in context.
- 3,019 sleep-and-check polling loops.

## The seven skills

Names are working names; final names, wording and layout are the builder's.

1. **Briefing an agent** (fires before spawning a subagent or teammate). One job, one result, then stop; state goes
   in files and PRs; a narrow brief (goal, files that matter, what's ruled out, no pasted history); stop every server
   you started before reporting; never end a turn "waiting for" a job. Prefer doing small things inline over spawning;
   fewer, smaller agents over many large parallel ones. Prints a short footer to paste into briefs.
   Why: the 117-hour agent; agents were 93% of cost.
2. **Waiting for free** (fires when a build, CI run, deploy or long script will take minutes). One background
   watcher that exits when the job is done and wakes the agent once; long scripts write a final DONE/FAILED line and a
   done marker; no sleep-and-check loops; never leave a big context idle. The three waiter traps, from real failures:
   - `pgrep -f "<pattern>"` in a wait loop matches the wait loop's own command line, so it never ends.
   - A waiter that greps an output file for "done" can fire at once on the *previous* run's "done" line; two runs
     then collide in one checkout.
   - A background job's completion notice doesn't always wake an idle agent; agents stalled 30–60 minutes this way.
   Why: 3,019 polling loops; 1,039 cache rebuilds.
3. **Context hygiene** (fires when a session is getting heavy, or when editing CLAUDE.md). Near ~250k tokens, write
   what matters to a handoff file and start fresh. Keep CLAUDE.md an index under ~20 KB; feature detail goes in a
   separate doc agents read only for the part they touch.
   Why: >400k calls were 71% of cost; the 32k → 113k starting context.
4. **Looking cheaply** (fires before screenshots or visual checks). Contact sheets instead of single frames, small
   images, one look per change; a short-lived reviewer looks and reports in words.
   Why: 6,574 screenshots, each re-read on every later turn.
5. **Merging in batches** (fires when merging a queue of PRs). Check a pre-resolved chain of PRs once at its tip
   instead of one CI run per PR; queue them in one call; retry a flaky test once and log it, two failures stop the
   queue; then fix the flake at its root (pin clocks and randomness in tests).
6. **Rulings become tests** (fires when the lead makes a judgment call: a naming rule, a limit, a "never do X").
   The ruling becomes a guard test the same turn, so next week's fresh agent can't quietly undo it. Agents don't
   remember your decisions; your test suite does.
7. **Audit your spend** (fires when asked where tokens went). A stdlib-only Python script, run locally, that reads
   `~/.claude/projects/**/*.jsonl` and prints counts and percentages only (never message content):
   - tokens by day and week, the mix (cache reads / cache writes / output / input), output share;
   - share of tokens and of estimated cost from calls over 400k context (cost weighting uses API list-price ratios
     internally; the report shows percentages, never dollars);
   - cache rebuilds after idle gaps (count, tokens, share);
   - the longest-lived sessions and their share;
   - median starting context of new sessions and agents, by day;
   - sleep-polling Bash calls and images in context.
   Starting point: Jon's October token counter, which
   handles the dedup by (message id, request id) and includes subagent logs.

## How it gets made

- **Decided by Jon:** public repo under the `coracle-us` GitHub account; Claude Code plugin; audience is leads of
  agent teams; tokens and percentages, no dollars; the post's job is installs; Jon posts the post himself.
- **Claude's calls (Jon can override):**
  - Repo name `coracle-us/agent-team-skills` (renaming is cheap before launch).
  - MIT licence; credited to Jon McBee / Coracle.
  - A README that leads with the principle and the numbers, then the two install commands, then one paragraph per
    skill.
  - This design doc is committed in the repo as `docs/design.md`.
- **Verify, don't assume:** the current Claude Code plugin and marketplace layout and install commands (check the
  Claude Code docs); `gh api user` must show coracle-us before any push (this machine has several GitHub accounts,
  routed by folder).

## The LinkedIn post

Under about 250 words, readable without "see more" for the hook. Hook: the October numbers and the principle. Middle:
the seven lessons, one line each with its strongest number. End: the install commands and the repo link, plus the
audit skill as a challenge ("run it on your own week"). Tokens and percentages only. No company, project or people
named except Jon. Delivered to Jon as text; he posts it.

## Outward-facing steps (Jon approves each)

Creating the public repo, the first push, and the post. Nothing is made public before Jon has read the repo.

## Settled after review (Claude's calls)

- **Audit fields.** The builder inspects real session logs to find the fields each metric needs (per-call context =
  input + cache read + cache write; sidechain/agent markers; tool_use blocks for Bash `sleep`; image blocks). A metric
  that can't be measured reliably is dropped or shipped marked "approximate", never guessed silently.
- **Cost weighting and rebuilds.** The same method as the original audit: Opus API list-price ratios (input 4,
  output 20, cache read 0.2, cache write 5–8 per million, depending on cache lifetime), shown only as percentages and
  labelled estimates. A "rebuild" is a call whose cache write is most of its context, coming more than 5 minutes after
  the previous call in the same session. The report states both rules in its footer.
- **Waiting mechanism.** Skills describe the pattern tool-agnostically (one waiter that exits when the job is done;
  done markers; never end a turn waiting on a job), then give Claude Code's current way to do it as the example:
  `run_in_background` for a job that notifies on exit, or a Monitor until-loop on a done marker. Agent teams are named
  as experimental where mentioned.
- **Scope.** Claude Code only. Skill 5 is written for any CI, with GitHub as the example.
- **Graceful fallback.** Skill 6 assumes a test runner exists; if none does, it records the ruling in the briefing's
  index and suggests the smallest test setup.
- **Testing.** Per skill: one fresh-subagent scenario without the skill and one with it, checked by reading the
  result. A repeatable `claude plugin eval` suite is optional, not required for launch. The audit script gets a unit
  test on a small synthetic log.

## Left to the builder

Skill names and wording, file layout inside the plugin, the audit script's structure and output format, README
design, and how each skill is tested (keep testing proportionate: a small with/without check per skill, not a
large evaluation).
