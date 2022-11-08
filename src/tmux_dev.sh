#!/bin/bash

session="Pymap"

tmux new-session -d -s $session

window=0

tmux rename-window -t $session:$window "API"
tmux send-keys -t $session:$window "poetry run task apiDev" C-m

tmux select-window -t $session:$window

tmux split-window -h
tmux send-keys "cd client && npm start" C-m

tmux split-window -v -t $session:$window.$window
tmux send-keys "poetry run task workerDev" C-m

tmux split-window -v -t $session:$window.2
tmux send-keys "redis-server" C-m

tmux attach-session -t $session
