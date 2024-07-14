# Source: https://juliu.is/a-simple-tmux/
# Gets the name of the current directory and removes periods, which tmux doesn’t like.
# If any session with the same name is open, it re-attaches to it.
# Otherwise, it checks if an .envrc file is present and starts a new tmux session using direnv exec.
# Otherwise, starts a new tmux session with that name.
function tat {
  name=$(basename `pwd` | sed -e 's/\.//g')

  if tmux ls 2>&1 | grep "$name"; then
    tmux attach -t "$name"
  elif [ -f .envrc ]; then
    direnv exec / tmux new-session -s "$name"
  else
    tmux new-session -s "$name"
  fi
}
