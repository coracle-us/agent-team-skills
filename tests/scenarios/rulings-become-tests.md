# Scenario: rulings-become-tests

Prompt: `rulings-become-tests.prompt.md`.
Passes when: a guard test is written the same turn (or, with no runner, a CLAUDE.md line plus the smallest setup);
CLAUDE.md gets one line pointing at it.

## Without
- Writes a 10-line CLAUDE.md section and a brief line: "That's the whole note."
- The guard test is offered as optional: "If you're fine with a two-minute addition, I'd also add one vitest guard."

## With
- Pass. Writes `src/oldNameGuard.test.ts` the same turn with the ruling quoted in the failure message; runs it and
  fixes or lists leftovers without loosening it; one CLAUDE.md line pointing at the test; one line to the user.
