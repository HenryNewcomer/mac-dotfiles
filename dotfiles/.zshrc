# >>> Henry's customizations
# --------------------------

# -------------
# Adds color as seen within Kitty
# -------------

# Enable color support of ls and also add handy aliases
if [ -x /usr/bin/dircolors ]; then
    test -r ~/.dircolors && eval "$(dircolors -b ~/.dircolors)" || eval "$(dircolors -b)"
    alias ls='ls --color=auto'
    alias dir='dir --color=auto'
    alias vdir='vdir --color=auto'

    alias grep='grep --color=auto'
    alias fgrep='fgrep --color=auto'
    alias egrep='egrep --color=auto'
fi

# Colored GCC warnings and errors
export GCC_COLORS='error=01;31:warning=01;35:note=01;36:caret=01;32:locus=01:quote=01'

# Set CLICOLOR if you want Ansi Colors in iTerm2
export CLICOLOR=1


# -------------
# Aliases
# -------------

# Custom aliases for important directory locations
alias dev="cd ~/dev/"
alias iris="cd ~/dev/iris && source .venv/bin/activate && python app.py --help"
alias ros="cd ~/dev/rosai && source .venv/bin/activate && python app.py --help"
alias rosai="cd ~/dev/rosai && source .venv/bin/activate"
alias echoai="cd ~/dev/echo && source .venv/bin/activate"
alias macdot="cd ~/dev/mac-dotfiles/"
alias merge="cd ~/dev/merge_code/"

# Git aliases
alias gs="git status"
alias gpull="git pull"
alias gpush="git push"
# prune_stashes

# Setup Python environment
alias setpy="python3 -m venv .venv && source .venv/bin/activate"
alias py="source .venv/bin/activate && python3"

# Generate a private key and a self-signed certificate. (For SSL in MAMP)
alias gencert="openssl req -x509 -newkey rsa:4096 -keyout localhost.key -out localhost.crt -days 365 -nodes -subj \"/CN=localhost\""

# Manually add environment variables for Python
export PATH="/opt/homebrew/bin/python3:$PATH"
export PATH="/Library/Frameworks/Python.framework/Versions/3.11/bin/python3:$PATH"
alias python=python3 # Super weird that I have to add this, but... ¯\_(ツ)_/¯

# Manually add environment variables for Emacs
export PATH="/Applications/Emacs.app/Contents/MacOS:$PATH"

# Access custom clean_ds_store() bash function to recursively remove .DS_Store from current dir and its children
# TODO: Just merge into mac-dotfiles project.
alias dsstore="bash ~/dev/mac-dotfiles/clean_ds_store.sh"

# Other aliases...
alias mazitree='cd ~/dev/work/pixelpeople/mazipro/mazipro-portal/public_html/wp-content/plugins/teamconnect/ && tree'


# -------------
# Set config values
# -------------

# Set colors for the prompt
autoload -U colors && colors

# Ignore duplicate commands in history
# This makes it so pressing UP doesn't keep showing the exact same command over and over,
# if they were used in succession.
setopt HIST_IGNORE_DUPS


# -------------
# Functions
# -------------

# Custom "webp" function to convert images to webp format
webp() {
    ~/dev/webp-converter/webp_converter.sh "$@"
}

# Only retain the X most recent stashes in the current repo.
function prune_stashes() {
    typeset -i retain_amount=30
    echo "Pruning stashes; retaining the $retain_amount most recent..."
    #echo "Current stash count: $(git stash list | wc -l)"
    git stash list | tail -n +$((retain_amount+1)) | cut -d: -f1 | xargs -r -n 1 git stash drop
    echo "Pruning complete.\n"
}


# -------------
# Work-related
# -------------

MAZI_DIR="$HOME/dev/work/pixelpeople/mazipro/mazipro-portal/"
alias mazi="cd $MAZI_DIR"

# Helper function to safely reset branch state
function __mazi_reset_branch_state() {
    local branch=$1
    # Abort any pending merges
    git merge --abort 2>/dev/null
    # Reset only tracked files to their original state
    git reset --hard "origin/$branch"
}

# Helper function to safely update a branch
function __mazi_update_branch() {
    local branch=$1
    echo "\nUpdating branch: $branch"

    # Try to checkout branch
    if ! git checkout "$branch"; then
        echo "Error: Failed to checkout $branch"
        return 1
    fi

    # Fetch latest changes for this branch specifically
    echo "Fetching updates for $branch..."
    if ! git fetch origin "$branch"; then
        echo "Error: Failed to fetch $branch"
        return 1
    fi

    # Show status and changes to be pulled
    git status

    # Get the number of commits behind
    local behind_count=$(git rev-list HEAD..origin/"$branch" --count)
    if [ $behind_count -gt 0 ]; then
        echo "\nNew changes to pull for $branch:"
        git log HEAD..origin/"$branch" --oneline

        # Pull changes with merge strategy
        echo "\nPulling updates..."
        if ! git merge --ff-only "origin/$branch"; then
            echo "Error: Failed to fast-forward merge $branch"
            return 1
        fi
    else
        echo "Branch $branch is up to date."
    fi

    # Reset to ensure clean state
    __mazi_reset_branch_state "$branch"

    echo "Successfully updated branch: $branch\n"
    return 0
}

# Main function to pull GitHub changes into core, local MaziPro branches
function update_local_mazipro_repo() {
    cd $MAZI_DIR || { echo "Error: Could not change to MAZI_DIR"; return 1; }
    echo "Current location: $(pwd)"

    # Store initial branch
    current_branch=$(git rev-parse --abbrev-ref HEAD)
    echo "Current branch: $current_branch\n"

    # Start update process
    echo "Fetching latest changes from GitHub..."
    if ! git fetch --all --prune; then
        echo "Error: Failed to fetch from remote"
        return 1
    fi

    # Check for both tracked and untracked changes
    if [ -n "$(git status --porcelain)" ]; then
        echo "Stashing current work (including untracked files)..."
        if ! git stash push --include-untracked -m "Pre-pull stash $(date)"; then
            echo "Error: Failed to stash changes"
            return 1
        fi
        stashed=true
        echo "Changes have been stashed."
    else
        echo "No changes to stash."
        stashed=false
    fi

    # Array of branches to update
    branches=("main" "staging-phase1" "main_phase2" "staging")

    # Update each branch
    for branch in "${branches[@]}"; do
        if ! __mazi_update_branch "$branch"; then
            echo "Error occurred while updating $branch"
            # Try to return to original branch
            git checkout "$current_branch"
            # Restore stashed changes if any
            if [[ $stashed == true ]]; then
                echo "Restoring stashed changes after error..."
                git stash pop
            fi
            return 1
        fi
    done

    echo "All core branches have been updated."
    echo "Returning to original branch: $current_branch..."

    # Return to original branch
    if ! __mazi_update_branch "$current_branch"; then
        echo "Error: Failed to return to $current_branch"
        return 1
    fi

    # Restore stashed changes if any
    if [[ $stashed == true ]]; then
        echo "Restoring stashed changes..."
        if ! git stash pop; then
            echo "Warning: Failed to restore stashed changes. Your changes are still in the stash."
            echo "You may need to resolve conflicts manually."
            return 1
        fi
    fi

    echo "\nRepository update complete.\n"

    # Prune old stashes
    prune_stashes

    return 0
}
alias mazipull='update_local_mazipro_repo'

# --------------------------
# <<< Henry's customizations