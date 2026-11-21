---
name: rulings-become-tests
description: Use when the user or lead makes a ruling that must keep holding, such as a naming rule, a limit, a "never do X" or "always Y", or says "note that" about a rule.
---

# Rulings become tests

**Agents don't remember your decisions; your test suite does.** A fresh agent tomorrow reads CLAUDE.md and its brief,
maybe. A test runs whether anyone read anything or not.

"Note that" about a rule means: write the guard test, now, in the same turn.

## The same turn

1. **Write a guard test** named after the ruling (`oldNameGuard.test.ts`). It fails on a violation, and its failure
   message quotes the ruling and where it came from: "The old name must never appear where users can see it (user,
   2026-11-20)."
2. **Run it.** If it finds existing violations, fix them if it's quick, or list them for the user. Don't weaken the
   test to make it pass.
3. **Add one line to CLAUDE.md** pointing at the test: "Old product name: never user-visible. Enforced by
   `src/oldNameGuard.test.ts`; fix the text, never the allowlist."
4. Tell the user in one line, and move on.

No test runner in the project? Put the ruling in CLAUDE.md as one line, and suggest the smallest setup that would
enforce it (one script in CI).

## Common mistakes

| Thought | Reality |
|---|---|
| "The user's in a hurry; the test is an optional extra" | It's two minutes, and the note alone will be skimmed |
| "I'll write the test later" | Later is a fresh agent that never heard the ruling |
| "A long CLAUDE.md section explains it well" | One line plus a test. Every agent pays to read every line |
