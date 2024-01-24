#!/bin/bash

session="Pymap"

tmux new-session -d -s $session

window=0

tmux rename-window -t $session:$window "Django"
tmux send-keys -t $session:$window "poetry run task server" C-m

tmux select-window -t $session:$window

tmux split-window -h
tmux send-keys "poetry run task monitor" C-m

tmux split-window -v -t $session:$window.$window
tmux send-keys "poetry run task worker" C-m

tmux split-window -v -t $session:$window.2
tmux send-keys "redis-server" C-m

tmux attach-session -t $session
