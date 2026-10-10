#!/usr/bin/env bash
# Usage: ./scripts/loadtest.sh [seconds]
END=$((SECONDS + ${1:-120}))
while [ $SECONDS -lt $END ]; do
  curl -s -o /dev/null http://localhost:8000/orders &
  sleep 0.05
done
wait
