# agent-team-skills Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A public Claude Code plugin of seven skills that stop the token leaks of leading a team of agents, plus a LinkedIn post that gets people to install it.

**Architecture:** One repo that is both the plugin and its own marketplace (`.claude-plugin/plugin.json` + `marketplace.json`, `source: "./"`). Six instruction-only skills and one skill that ships a stdlib-only Python audit script. Skills are tested the writing-skills way: a fresh agent on a scenario without the skill, then with it.

**Tech Stack:** Claude Code plugin format, Markdown SKILL.md files, Python 3 stdlib (`unittest`), `claude plugin validate|details`.

**Spec:** `docs/design.md` (the approved design; the private original also lists the names that must never appear).

## Global Constraints

- Audience: someone **leading a team of Claude Code agents**. Claude Code only.
- No dollar figures anywhere. Tokens, counts and percentages only; percentages of cost are fine.
- Nothing that identifies the original project or employer: no company, project, game or coworker names, internal paths, script names, URLs or repo names. "A multiplayer browser game, built in 12 days" is the most specific it gets.
- Use only the measured numbers in the design's "The numbers" section. "A third to half was avoidable" is left out.
- Short SKILL.md files with precise descriptions (each starts "Use when", under 300 characters, describes the moment, not the workflow). Each SKILL.md under ~800 words.
- The audit script prints counts and percentages only, never message content or project paths; stdlib only; no network.
- Repo: `coracle-us/agent-team-skills`, MIT, credited to Jon McBee / Coracle. Local path `~/Documents/GitHub/coracle/agent-team-skills`; commits as jon@coracle.us.
- Nothing is pushed or made public until Jon approves (Task 10).

## Review Focus

1. **Logs with lines that aren't valid JSON, or entries without `usage`** (truncated writes, other entry types): skipped silently, counted in a "lines skipped" footer. Test in Task 2.
2. **The same response logged several times** (streamed entries with the same message id + request id): counted once. Test in Task 2.
3. **A window with no data** (empty `~/.claude/projects`, or a week with no sessions): prints "no usage in this window", exits 0, no division by zero. Test in Task 2.
4. **The report leaking content or paths**: no message text, tool input or project folder name appears in the output. Test in Task 2.
5. **Old transcripts already deleted** by Claude Code's cleanup (`cleanupPeriodDays`, default 30): the report states the earliest date it actually found, so a short total isn't mistaken for low use. Test in Task 2.

---

### Task 1: Scaffold the plugin

**Files:**
- Create: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `LICENSE`, `README.md` (stub: title + one line), `.gitignore`, `docs/design.md`

**Interfaces:**
- Produces: plugin name `agent-team-skills`, marketplace name `agent-team-skills`; skills live at `skills/<skill-name>/SKILL.md`.

- [ ] **Step 1:** Write `plugin.json`: name `agent-team-skills`, version `0.1.0`, description "Skills for leading a team of Claude Code agents without paying for them to remember.", author Jon McBee, homepage/repository `https://github.com/coracle-us/agent-team-skills`, license MIT. Write `marketplace.json` with owner Jon McBee / Coracle and one plugin entry, `source: "./"`. Use the superpowers plugin's two files as the shape reference.
- [ ] **Step 2:** Copy the approved design into `docs/design.md`, with the anti-goal line's list of real names replaced by "no company, project, game or coworker names", and the starting-point script described generically.
- [ ] **Step 3:** Run `claude plugin validate .`. Expected: valid (no skills yet is fine; if it requires one, add the Task 2 skill folder first).
- [ ] **Step 4:** Commit: `chore: scaffold agent-team-skills plugin`.

### Task 2: The audit script

**Files:**
- Create: `skills/audit-your-spend/scripts/audit.py`
- Test: `tests/test_audit.py`, `tests/fixtures/` (small synthetic `.jsonl` logs written by the test's `setUp`, not checked in)

**Interfaces:**
- Produces:
  - `load_calls(root: str, since: date, until: date) -> tuple[list[Call], Stats]`. `Call` is a dataclass: `session: str` (file stem), `agent: bool` (sidechain or under a `subagents/` folder), `ts: datetime`, `model: str`, `input: int`, `output: int`, `cache_read: int`, `cache_write_5m: int`, `cache_write_1h: int`, `context: int` (input + cache_read + both writes), `sleep_polls: int`, `images: int`. `Stats`: `files_scanned`, `lines_skipped`, `earliest`, `latest`.
  - `build_report(calls: list[Call], stats: Stats) -> dict` and `render(report: dict) -> str`.
  - CLI: `python3 audit.py [--since YYYY-MM-DD] [--until YYYY-MM-DD] [--root PATH] [--json]`; default window the last 7 UTC days, `--until` inclusive, root `~/.claude/projects`.

- [ ] **Step 1: Survey real fields.** Run a throwaway one-liner over a handful of real logs that prints only key paths and block types (never values) to confirm where these live: `message.usage.cache_creation.ephemeral_5m_input_tokens` / `ephemeral_1h_input_tokens`, `isSidechain`, `tool_use` blocks with `name == "Bash"` and `input.command`, `image` blocks inside user content and inside `tool_result` content. Record any field that differs from this list in a comment at the top of `audit.py`; drop or mark "approximate" any metric whose field doesn't exist.
- [ ] **Step 2: Write the failing tests.** In `tests/test_audit.py` (`unittest`), each building a temp root with synthetic sessions:
  - `test_dedup_by_message_and_request`: the same usage line three times counts once.
  - `test_skips_bad_lines`: a non-JSON line and a line without usage are skipped; `Stats.lines_skipped == 2`.
  - `test_mix_percentages`: tokens 960 cache read, 30 cache write, 10 output → report mix 96.0 / 3.0 / 1.0.
  - `test_heavy_calls_share`: one call at 500k context and one at 100k → heavy (>400k) share of calls 50%, share of cost computed with weights input 4, output 20, cache read 0.2, cache write 5m 5, 1h 8.
  - `test_rebuild_detection`: in one session, a call at t=0 and a call at t=6 min whose cache write is 90% of its 300k context → 1 rebuild; the same at t=4 min → 0; a session's first call is never a rebuild; contexts under 20k are ignored.
  - `test_starting_context_median`: three sessions starting at 30k, 40k, 120k → median 40k; lead and agent sessions reported separately.
  - `test_sleep_polls_and_images`: a Bash command `sleep 30 && gh run view` counts 1 poll; `sleep` inside `run_in_background` commands still counts; two image blocks (one in a tool_result) count 2.
  - `test_longest_sessions`: top sessions sorted by duration, shown by short id (first 8 chars) with hours and share of cost.
  - `test_empty_window`: no calls → `render` says "no usage in this window", no exception.
  - `test_no_content_or_paths_in_output`: synthetic log containing the text `SECRET-TEXT` and project folder `-Users-someone-private` → neither appears in `render()` or `--json` output.
  - `test_reports_earliest_date`: the footer states the earliest and latest timestamps found.
- [ ] **Step 3:** Run `python3 -m unittest -v tests/test_audit.py`. Expected: all FAIL (import error).
- [ ] **Step 4: Implement `audit.py`.** Stream files line by line (never load a whole file); filter on `'"usage"' in line` before `json.loads`, like the October counter. The rendered report has, in order: totals and mix; tokens by day and by ISO week; agents vs lead share of tokens and cost; heavy-call share; rebuilds (count, tokens, share of cost); top 5 longest sessions; median starting context by day (lead / agent); sleep polls; images; a footer stating the weighting rule, the rebuild rule ("cache write ≥ 50% of a ≥ 20k context, > 5 min after the previous call in the session"), that cost shares are estimates, files scanned, lines skipped, and the date range found.
- [ ] **Step 5:** Run the tests. Expected: all PASS.
- [ ] **Step 6:** Commit: `feat: audit script for Claude Code token spend`.

### Task 3: The audit-your-spend skill, checked against October

**Files:**
- Create: `skills/audit-your-spend/SKILL.md`

**Interfaces:**
- Consumes: the CLI from Task 2.

- [ ] **Step 1:** Write `SKILL.md`. Description: "Use when asked where Claude Code tokens went, why usage is high, or to check a week's spend for leaks." Body: run the script (with `${CLAUDE_PLUGIN_ROOT}/skills/audit-your-spend/scripts/audit.py`), read the report back in plain words, map each leak it finds to the skill that fixes it (rebuilds and polls → waiting-for-free, heavy calls and starting context → context-hygiene, long sessions → briefing-agents, images → looking-cheaply), and never paste the report anywhere public without the user's say.
- [ ] **Step 2:** Run on Jon's machine: `python3 skills/audit-your-spend/scripts/audit.py --since 2026-10-01 --until 2026-10-31`. Expected: total 25,461,485,789 tokens and output 0.10%. If lower, the footer's earliest date must explain it (transcript cleanup); then compare the days still present against the October daily CSV from the original measurement, which must match day for day. Don't commit the output.
- [ ] **Step 3:** Commit: `feat: audit-your-spend skill`.

### Tasks 4–9: The six behaviour skills

One task per skill, each with the same five steps. Every SKILL.md opens with the one-line principle it serves, gives the rule, the steps for the moment, the "why" as one or two measured numbers from the design, and nothing else.

- [ ] **Step 1: Baseline.** Dispatch a fresh agent (model sonnet, no plugin) with the skill's scenario below. Save what it did, in a few lines, to `tests/scenarios/<skill>.md` under "Without".
- [ ] **Step 2:** Write `skills/<skill>/SKILL.md` aimed at the failures the baseline showed.
- [ ] **Step 3: With the skill.** Run the same scenario with the skill's text supplied. Record under "With". Expected: the listed pass condition holds.
- [ ] **Step 4:** If it doesn't, tighten the skill and repeat Step 3 once more; if it still fails, note it in the scenario file and bring it to Jon.
- [ ] **Step 5:** Commit: `feat: <skill> skill`.

| Task | Skill folder | Description starts | Scenario | Passes when |
|---|---|---|---|---|
| 4 | `briefing-agents` | Use when about to spawn a subagent or teammate, or writing an agent's brief | "Write the brief for an agent that fixes a failing test and opens a PR." The prompt includes 2 pages of project history. | The brief is narrow (goal, files, ruled out, no pasted history), says one job then stop, stop servers before reporting, never end a turn waiting on a job; ends with the paste-ready footer. |
| 5 | `waiting-for-free` | Use when a build, CI run, deploy or script will take more than a minute or two | "CI takes 12 minutes. Wait for it, then merge if green." | One waiter that exits when CI finishes; no sleep-and-check loop; no `pgrep -f` self-match; doesn't end the turn waiting. All three waiter traps appear in the skill. |
| 6 | `context-hygiene` | Use when a session's context is getting large, or when adding to CLAUDE.md | Two prompts: "We're at 300k context; next, build feature X." and "Add the full details of feature Y to CLAUDE.md." | First: writes a handoff file and recommends a fresh session. Second: puts the detail in a separate doc and adds one index line to CLAUDE.md. |
| 7 | `looking-cheaply` | Use when about to take screenshots or check visual output | "Check 12 UI states look right after this change." | Builds one contact sheet (or hands review to a short-lived reviewer that reports in words); no 12 separate full-size screenshots. |
| 8 | `merging-in-batches` | Use when merging several PRs, or when a test fails intermittently | "Merge 5 stacked PRs; CI takes 40 minutes; one e2e test is flaky." | Checks the chain tip once; queues all in one call; retries the flake once and logs it; proposes fixing the flake's root (pinned clock or seed). |
| 9 | `rulings-become-tests` | Use when the lead makes a judgment call that must keep holding | "The lead says: never show the old product name anywhere users can see. Note that." | Writes a guard test the same turn (or, with no test runner, records it in the briefing index and suggests the smallest setup), not just a note. |

### Task 10: README, post, privacy check, local install, then Jon

**Files:**
- Modify: `README.md`
- Create: `tests/test_repo.py`
- Outside the repo: `<scratchpad>/agent-team-skills/linkedin-post.md`, `<scratchpad>/agent-team-skills/privacy-scan.sh` (holds the real names to forbid, so it never ships)

- [ ] **Step 1:** Write `README.md`: the principle ("You pay for agents to remember, not to work"), the October numbers, the two install commands, one paragraph per skill with its number, how to run the audit on your own week, licence.
- [ ] **Step 2:** Write `tests/test_repo.py`: `test_no_dollar_figures` (no `\$\s?\d` in any tracked file); `test_skill_frontmatter` (every `skills/*/SKILL.md` has `name` matching its folder and a description starting "Use when" under 300 characters); `test_skill_length` (each SKILL.md under 800 words). Run `python3 -m unittest -v`. Expected: all PASS.
- [ ] **Step 3:** Run the private `privacy-scan.sh` (case-insensitive `rg` over the repo and its git history for the forbidden names from the private design, plus `/Users/`). Expected: no matches.
- [ ] **Step 4:** Run `claude plugin validate .` and `claude plugin details ./` (or by name after Step 5). Expected: valid; record the projected token cost for the README.
- [ ] **Step 5:** Install locally: `claude plugin marketplace add ~/Documents/GitHub/coracle/agent-team-skills` then `claude plugin install agent-team-skills@agent-team-skills`; confirm the seven skills list; then uninstall and remove the local marketplace so it doesn't linger.
- [ ] **Step 6:** Write the LinkedIn post draft (under ~250 words, per the design) to the scratchpad file.
- [ ] **Step 7:** Commit: `docs: README and repo checks`.
- [ ] **Step 8: Stop and hand to Jon.** Show the repo, the README and the post. Only on his OK: confirm `GH_CONFIG_DIR=~/.config/gh-coracle gh api user` shows coracle-us, then `gh repo create coracle-us/agent-team-skills --public --source . --push`. The post is his to publish.
