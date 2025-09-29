#!/usr/bin/env bash
cd "$HOME/classroom"
while true; do
  "$HOME/classroom/venv/bin/python" "$HOME/classroom/GCR.py" >/dev/null 2>&1 || echo "fetch failed at $(date)" >> "$HOME/classroom/fetch.log"
  sleep 300   # 5 minutes
done
