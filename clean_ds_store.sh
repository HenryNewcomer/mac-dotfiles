#!/bin/bash

# Function to show spinner with count
show_spinner() {
    local spinstr='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'

    while kill -0 "$2" 2>/dev/null; do
        local count=$(< "$1")
        local temp=${spinstr#?}
        printf "\r[%c] Searching... (found %d .DS_Store files)" "$spinstr" "$count"
        spinstr=$temp${spinstr%"$temp"}
        sleep 0.1
    done
    printf "\r"
}

# Function to search and remove .DS_Store files
clean_ds_store() {
    echo "Searching for .DS_Store files..."

    # Create temporary file for counting
    local count_file=$(mktemp)
    echo "0" > "$count_file"

    # Start the search and remove process in background
    (
        find . \
            -type f \
            -name ".DS_Store" \
            -not \( -path "*/.config/*" -prune \) \
            -print0 2>/dev/null | \
        tee >(tr -cd '\0' | wc -c > "$count_file") | \
        xargs -0 -P 4 rm 2>/dev/null
    ) &

    # Show spinner while processing
    show_spinner "$count_file" $!

    # Get final count
    local total=$(< "$count_file")
    rm "$count_file"

    echo -e "\nSearch and removal completed."

    if [[ $total -gt 0 ]]; then
        echo "Total .DS_Store files removed: $total"
    else
        echo "No .DS_Store files found."
    fi
}

# Execute the function if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    clean_ds_store
fi
