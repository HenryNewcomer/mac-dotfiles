#!/bin/bash

# Function to search and remove .DS_Store files, excluding directories without permission
clean_ds_store() {
  # Initialize variables
  local count=0
  local file_list=()

  # Find all .DS_Store files, excluding permission-denied directories
  while IFS= read -r -d $'\0' file; do
    file_list+=("$file")
    ((count++))
  done < <(find . -name ".DS_Store" -not \( -path "*/.config/*" -prune \) -print0 2>/dev/null)

  # Display found files and delete them
  if [[ $count -gt 0 ]]; then
    echo "Found $count .DS_Store file(s):"
    for file in "${file_list[@]}"; do
      echo "$file"
      rm "$file"
    done
    echo "Total .DS_Store files removed: $count"
  else
    echo "No .DS_Store files found."
  fi
}

# Execute the function if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  clean_ds_store
fi
