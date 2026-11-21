#!/bin/zsh
# Run each scenario prompt headless in an empty folder (no project CLAUDE.md, no project memory).
# Usage: zsh tests/run-scenarios.sh <out-dir> [skills-root]   (with skills-root: each scenario runs with skills/<name>/SKILL.md appended)
set -u
HERE=${0:A:h}; OUT=${1:A}; WITH=${2:-}; mkdir -p "$OUT"
EMPTY=$(mktemp -d)
for p in $HERE/scenarios/*.prompt.md; do
  name=${p:t:r:r}
  extra=()
  [[ -n $WITH ]] && extra=(--append-system-prompt "$(cat $WITH/$name/SKILL.md)")
  ( cd $EMPTY && claude -p --model sonnet "${extra[@]}" < $p > $OUT/$name.md 2>&1 ) &
done
wait; rm -rf $EMPTY; echo DONE
