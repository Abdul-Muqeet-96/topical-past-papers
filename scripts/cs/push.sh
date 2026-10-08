#!/bin/sh
# Push the CS run's branch; on a network error retry 4 times (2, 4, 8, 16 s).
b=claude/cs-9618-booklets
[ "$(git rev-parse --abbrev-ref HEAD)" = "$b" ] || { echo "not on $b"; exit 1; }
for w in 0 2 4 8 16; do
  [ "$w" -gt 0 ] && sleep "$w"
  if git push -u origin "$b" 2>&1 | tail -2; then
    git rev-parse --verify -q "origin/$b" >/dev/null && [ "$(git rev-parse HEAD)" = "$(git rev-parse origin/$b)" ] && { echo "pushed $(git rev-parse --short HEAD)"; exit 0; }
  fi
done
echo "PUSH FAILED"; exit 1
