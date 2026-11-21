# Scenario: context-hygiene

Prompt: `context-hygiene.prompt.md`.
Passes when: A writes a handoff file and recommends a fresh session; B puts the detail in a separate doc and adds
one index line to CLAUDE.md.

## Without
- A fails: "300k of 1M is not a problem, so I wouldn't `/clear` or compact." Saves notes, then plans and dispatches
  the CSV feature from the heavy session.
- B passes: `docs/notifications.md` plus a pointer, though the pointer is an 8-line section with invariants.

## With
- Pass. A: handoff file with in-flight / decisions / waiting / first step; stops servers; tells the user to start a
  fresh session and does not dispatch from the heavy one. B: `docs/notifications.md` plus exactly one index line;
  flags the 140 KB file and offers (doesn't do) the split.
