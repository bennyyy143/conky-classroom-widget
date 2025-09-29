#!/bin/bash
# Start your fetch loop in the background
nohup "$HOME/classroom/run_fetch_loop.sh" >/dev/null 2>&1 &

# Start Conky with your classroom config
conky -c "$HOME/.config/conky/classroom.conf" -d
