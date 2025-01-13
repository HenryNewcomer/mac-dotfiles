# >>> Henry's customizations
# --------------------------


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


### Adds color as seen within Kitty

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

# Set colors for the prompt
autoload -U colors && colors

# Ignore duplicate commands in history
# This makes it so pressing UP doesn't keep showing the exact same command over and over,
# if they were used in succession.
setopt HIST_IGNORE_DUPS

# Custom "webp" function to convert images to webp format
webp() {
    ~/dev/webp-converter/webp_converter.sh "$@"
}

# Only retain the X most recent stashes in the current repo.
function prune_stashes() {
    typeset -i retain_amount=10
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

# Pull GitHub changes into the core, local MaziPro branches.
function update_local_mazipro_repo() {
    cd $MAZI_DIR || { echo "Error: Could not change to MAZI_DIR"; return 1; }
    echo "Current location: $(pwd)"

    # Store initial branch
    current_branch=$(git rev-parse --abbrev-ref HEAD)
    echo "Current branch: $current_branch\n"

    # Function to clean working directory
    clean_working_directory() {
        # Reset any changes in tracked files
        git reset --hard HEAD
        # Remove untracked files and directories
        git clean -fd
    }

    # Function to safely update a branch
    update_branch() {
        local branch=$1
        echo "\nUpdating branch: $branch"

        # Try to checkout branch
        if ! git checkout "$branch"; then
            echo "Error: Failed to checkout $branch"
            return 1
        }

        # Clean working directory before pull
        clean_working_directory

        # Pull latest changes
        if ! git pull origin "$branch"; then
            echo "Error: Failed to pull latest changes for $branch"
            return 1
        }

        # Clean again after pull to ensure no artifacts remain
        clean_working_directory

        echo "Successfully updated branch: $branch\n"
        return 0
    }

    # Start update process
    echo "Fetching latest changes from GitHub..."
    git fetch || { echo "Error: Failed to fetch from remote"; return 1; }

    # Check for local changes
    if ! git diff-index --quiet HEAD --; then
        echo "Stashing current work..."
        if ! git stash save -u "Pre-pull stash $(date)"; then
            echo "Error: Failed to stash changes"
            return 1
        fi
        stashed=true
    else
        echo "No changes to stash."
        stashed=false
    fi

    # Array of branches to update
    branches=("main" "staging-phase1" "main_phase2" "staging")

    # Update each branch
    for branch in "${branches[@]}"; do
        if ! update_branch "$branch"; then
            echo "Error occurred while updating $branch"
            # Try to return to original branch
            git checkout "$current_branch"
            # Restore stashed changes if any
            if [[ $stashed == true ]]; then
                git stash pop
            fi
            return 1
        fi
    done

    echo "All core branches have been updated."
    echo "Returning to original branch: $current_branch..."

    # Return to original branch
    if ! git checkout "$current_branch"; then
        echo "Error: Failed to return to $current_branch"
        return 1
    fi

    # Clean working directory before applying stash
    clean_working_directory

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