# >>> Henry's customizations

# Custom aliases
alias dev="cd ~/dev/"
alias ros="cd ~/dev/rosai && source .venv/bin/activate && python app.py --help"
# Setup Python environment
alias setpy="python3 -m venv .venv && source .venv/bin/activate"
alias py="source .venv/bin/activate && python3"
# Generate a private key and a self-signed certificate. (For SSL in MAMP)
alias gencert="openssl req -x509 -newkey rsa:4096 -keyout localhost.key -out localhost.crt -days 365 -nodes -subj \"/CN=localhost\""

# Manually add environment variables for Python
export PATH="/opt/homebrew/bin/python3:$PATH"
export PATH="/Library/Frameworks/Python.framework/Versions/3.11/bin/python3:$PATH"
alias python=python3

# Manually add environment variables for Emacs
export PATH="/Applications/Emacs.app/Contents/MacOS:$PATH"

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

# <<< Henry's customizations