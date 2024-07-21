#!/bin/bash

# ANSI color codes for styled output
HEADER='\033[95m'
OKBLUE='\033[94m'
OKGREEN='\033[92m'
WARNING='\033[93m'
ORANGE='\033[38;5;208m'
FAIL='\033[91m'
ENDC='\033[0m'
BOLD='\033[1m'
UNDERLINE='\033[4m'
CYAN='\033[96m'

# Symbols for visual indicators
CHECK='✓'
CROSS='✗'
ARROW='→'

# Custom tags for dotfiles
CUSTOM_START_TAG="# >>> Henry's customizations"
CUSTOM_END_TAG="# <<< Henry's customizations"

# URLs for downloads
FIRA_CODE_URL="https://github.com/tonsky/FiraCode/releases/download/6.2/Fira_Code_v6.2.zip"
KITTY_ICON_REPO_URL="https://github.com/k0nserv/kitty-icon/archive/refs/heads/master.zip"
EMACS_RSS_URL="https://emacsformacosx.com/atom/release"

# Global mapping of applications to install
declare -A APPLICATIONS
APPLICATIONS=(
    ["kitty,name"]="Kitty"
    ["kitty,install_method"]="homebrew"
    ["kitty,locations"]="/Applications/kitty.app /opt/homebrew/bin/kitty"
    ["vim,name"]="Vim"
    ["vim,install_method"]="homebrew"
    ["vim,locations"]="/usr/bin/vim /opt/homebrew/bin/vim"
    ["nvim,name"]="Neovim"
    ["nvim,install_method"]="homebrew"
    ["nvim,locations"]="/usr/local/bin/nvim /opt/homebrew/bin/nvim"
    ["zsh,name"]="Zsh"
    ["zsh,install_method"]="homebrew"
    ["zsh,locations"]="/bin/zsh /usr/local/bin/zsh /opt/homebrew/bin/zsh"
    ["emacs,name"]="Emacs"
    ["emacs,install_method"]="custom"
    ["emacs,locations"]="/Applications/Emacs.app"
)

print_styled() {
    local text="$1"
    local color="$2"
    local bold="$3"
    local underline="$4"
    local style="$color"
    [[ "$bold" == "true" ]] && style="${style}${BOLD}"
    [[ "$underline" == "true" ]] && style="${style}${UNDERLINE}"
    echo -e "${style}${text}${ENDC}"
}

print_header() {
    echo -e "${CYAN}
███╗   ███╗ █████╗  ██████╗ ██████╗ ███████╗    ██████╗  ██████╗ ████████╗███████╗██╗██╗     ███████╗███████╗
████╗ ████║██╔══██╗██╔════╝██╔═══██╗██╔════╝    ██╔══██╗██╔═══██╗╚══██╔══╝██╔════╝██║██║     ██╔════╝██╔════╝
██╔████╔██║███████║██║     ██║   ██║███████╗    ██║  ██║██║   ██║   ██║   █████╗  ██║██║     █████╗  ███████╗
██║╚██╔╝██║██╔══██║██║     ██║   ██║╚════██║    ██║  ██║██║   ██║   ██║   ██╔══╝  ██║██║     ██╔══╝  ╚════██║
██║ ╚═╝ ██║██║  ██║╚██████╗╚██████╔╝███████║    ██████╔╝╚██████╔╝   ██║   ██║     ██║███████╗███████╗███████║
╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝    ╚═════╝  ╚═════╝    ╚═╝   ╚═╝     ╚═╝╚══════╝╚══════╝╚══════╝
${ENDC}
\t${OKBLUE}by Henry Newcomer${ENDC}
${CYAN}=============================================================================================================
${ENDC}"
}

create_backup_dir() {
    local script_dir="$1"
    local standalone="$2"
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_dir

    if [[ "$standalone" == "true" ]]; then
        backup_dir="${script_dir}/backups/_standalones/${timestamp}"
    else
        backup_dir="${script_dir}/backups/${timestamp}"
    fi

    mkdir -p "$backup_dir"
    echo "$backup_dir"
}

run_command() {
    "$@"
}

download_file() {
    local url="$1"
    local destination="$2"
    curl -L -o "$destination" "$url"
}

extract_zip() {
    local zip_path="$1"
    local extract_to="$2"
    unzip -q "$zip_path" -d "$extract_to"
}

install_homebrew() {
    print_styled "\n$ARROW Checking Homebrew installation..." "$HEADER" "true"

    if command -v brew >/dev/null 2>&1; then
        print_styled "$CHECK Homebrew is already installed. Updating..." "$OKGREEN"
        brew update
    else
        print_styled "Homebrew not found. Installing..." "$WARNING"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi

    if [[ $? -eq 0 ]]; then
        print_styled "$CHECK Homebrew installed/updated successfully" "$OKGREEN"
        return 0
    else
        print_styled "$CROSS Homebrew installation/update failed" "$FAIL"
        return 1
    fi
}

install_brew_package() {
    local package="$1"
    print_styled "$ARROW Installing $package..." "$OKBLUE"
    if brew install "$package"; then
        print_styled "$CHECK $package installed successfully" "$OKGREEN"
    else
        print_styled "$CROSS $package installation failed" "$FAIL"
    fi
}

install_fira_code_font() {
    local script_dir="$1"
    print_styled "\n$ARROW Installing Fira Code font..." "$HEADER" "true"
    local downloads_dir="${script_dir}/downloads/other"
    mkdir -p "$downloads_dir"
    local font_zip="${downloads_dir}/FiraCode.zip"
    local font_dir="${HOME}/Library/Fonts"

    if download_file "$FIRA_CODE_URL" "$font_zip" && extract_zip "$font_zip" "$font_dir"; then
        print_styled "$CHECK Fira Code font installed successfully" "$OKGREEN"
    else
        print_styled "$CROSS Fira Code font installation failed" "$FAIL"
    fi
}

install_kitty() {
    local script_dir="$1"
    print_styled "\n$ARROW Installing Kitty..." "$HEADER" "true"

    # Check if Kitty is already installed
    if brew list kitty &>/dev/null; then
        print_styled "$CHECK Kitty is already installed. Updating..." "$OKGREEN"
        brew upgrade kitty
    else
        print_styled "Installing Kitty..." "$OKBLUE"
        brew install kitty
    fi

    if [ $? -eq 0 ]; then
        print_styled "$CHECK Kitty installed successfully" "$OKGREEN"
        # Install the custom icon
        install_kitty_icon "$script_dir"
    else
        print_styled "$CROSS Kitty installation failed" "$FAIL"
    fi
}

install_kitty_icon() {
    local script_dir="$1"
    print_styled "\n$ARROW Installing custom Kitty icon..." "$HEADER" "true"
    local downloads_dir="${script_dir}/downloads/repos"
    mkdir -p "$downloads_dir"
    local kitty_icon_zip="${downloads_dir}/kitty-icon.zip"

    if download_file "$KITTY_ICON_REPO_URL" "$kitty_icon_zip" && extract_zip "$kitty_icon_zip" "$downloads_dir"; then
        local kitty_icon_dir=$(find "$downloads_dir" -type d -name "kitty-icon-*" | head -n 1)
        local icon_path="${kitty_icon_dir}/build/neue_outrun.icns"

        if [ -f "$icon_path" ]; then
            local kitty_config_dir="${HOME}/.config/kitty"
            mkdir -p "$kitty_config_dir"
            local dest_icon_path="${kitty_config_dir}/kitty.app.icns"
            cp "$icon_path" "$dest_icon_path"

            print_styled "$CHECK Custom Kitty icon installed successfully" "$OKGREEN"
            print_styled "The icon will be applied automatically when Kitty starts." "$OKBLUE"
            print_styled "You may need to restart Kitty for the changes to take effect." "$WARNING"

            # Clear icon cache and restart Dock
            rm -rf /var/folders/*/*/*/com.apple.dock.iconcache
            killall Dock
        else
            print_styled "$CROSS neue_outrun.icns not found in the downloaded repository" "$FAIL"
        fi
    else
        print_styled "$CROSS Custom Kitty icon installation failed" "$FAIL"
    fi
}

install_emacs() {
    local script_dir="$1"
    print_styled "\n$ARROW Installing Emacs..." "$HEADER" "true"

    local emacs_app_path="/Applications/Emacs.app"
    if [[ -d "$emacs_app_path" ]]; then
        print_styled "$CHECK Emacs is already installed. Skipping installation." "$OKGREEN"
        print_styled " >> Please check for updates manually. <<" "$ORANGE"
        return
    fi

    local rss_content=$(curl -s "$EMACS_RSS_URL")
    local download_url=$(echo "$rss_content" | grep -oP '(?<=<link href=")[^"]*' | head -n 1)
    local version=$(echo "$rss_content" | grep -oP '(?<=<title>)[^<]*' | head -n 1)

    local downloads_dir="${script_dir}/downloads/emacs"
    mkdir -p "$downloads_dir"
    local dmg_path="${downloads_dir}/Emacs-${version}.dmg"

    print_styled "Downloading Emacs ${version}..." "$OKBLUE"
    if download_file "$download_url" "$dmg_path"; then
        print_styled "Mounting Emacs DMG..." "$OKBLUE"
        hdiutil attach "$dmg_path" > /dev/null

        print_styled "Installing Emacs..." "$OKBLUE"
        cp -R "/Volumes/Emacs/Emacs.app" "/Applications/"

        print_styled "Unmounting Emacs DMG..." "$OKBLUE"
        hdiutil detach "/Volumes/Emacs" > /dev/null

        print_styled "$CHECK Emacs ${version} installed successfully" "$OKGREEN"
    else
        print_styled "$CROSS Emacs installation failed" "$FAIL"
    fi
}

install_software() {
    local script_dir="$1"

    if ! install_homebrew; then
        print_styled "Homebrew installation failed. Skipping package installations." "$FAIL"
        return
    fi

    install_fira_code_font "$script_dir"

    for app in "${!APPLICATIONS[@]}"; do
        IFS=',' read -r key field <<< "$app"
        if [[ "$field" == "name" ]]; then
            local name="${APPLICATIONS[$app]}"
            local install_method="${APPLICATIONS[${key},install_method]}"
            local locations="${APPLICATIONS[${key},locations]}"

            if [[ "$install_method" == "homebrew" ]]; then
                if [[ "$key" == "kitty" ]]; then
                    install_kitty "$script_dir"
                elif ! is_package_installed "$locations"; then
                    install_brew_package "$key"
                else
                    print_styled "$CHECK $name is already installed. Updating..." "$OKGREEN"
                    brew upgrade "$key"
                fi
            elif [[ "$install_method" == "custom" && "$key" == "emacs" ]]; then
                install_emacs "$script_dir"
            fi
        fi
    done

    # Add an extra blank line after software installation
    echo
}

is_package_installed() {
    local locations="$1"
    for location in $locations; do
        if [[ -e "$location" ]]; then
            return 0
        fi
    done
    return 1
}

extract_custom_sections() {
    local content="$1"
    sed -n "/$CUSTOM_START_TAG/,/$CUSTOM_END_TAG/p" <<< "$content"
}

get_dotfiles_list() {
    local dotfiles_dir="$1"
    find "$dotfiles_dir" -type f
}

backup_dotfiles() {
    local script_dir="$1"
    local home_dir="$2"
    local standalone="$3"
    local dotfiles_dir="${script_dir}/dotfiles"
    local backup_dir=$(create_backup_dir "$script_dir" "$standalone")

    print_styled "\n================================================" "$HEADER" "true"
    print_styled "Backing up Dotfiles" "$HEADER" "true"
    print_styled "================================================\n" "$HEADER" "true"

    local success_count=0
    local fail_count=0

    while IFS= read -r dotfile; do
        local rel_path="${dotfile#$dotfiles_dir/}"
        local src_path="${home_dir}/${rel_path}"
        local dest_path="${backup_dir}/${rel_path}"

        print_styled "Backing up: ${rel_path}" "$OKBLUE"

        if [[ -f "$src_path" ]]; then
            mkdir -p "$(dirname "$dest_path")"
            if cp "$src_path" "$dest_path"; then
                print_styled "  $CHECK Backed up successfully" "$OKGREEN"
                ((success_count++))
            else
                print_styled "  $CROSS Backup failed" "$FAIL"
                ((fail_count++))
            fi
        else
            print_styled "  $CROSS Source file not found" "$WARNING"
            ((fail_count++))
        fi

        echo  # Empty line for readability
    done < <(get_dotfiles_list "$dotfiles_dir")

    print_styled "\nBackup Summary:" "$HEADER" "true"
    print_styled "$CHECK Successfully backed up: $success_count" "$OKGREEN"
    if [[ $fail_count -gt 0 ]]; then
        print_styled "$CROSS Failed to back up: $fail_count" "$FAIL"
    fi
    print_styled "Backup directory: $backup_dir" "$WARNING"

    echo "$success_count $fail_count"
}

process_dotfiles() {
    local script_dir="$1"
    local home_dir="$2"
    local backup_dir="$3"
    local dotfiles_dir="${script_dir}/dotfiles"
    local success_count=0
    local fail_count=0

    print_styled "\n================================================" "$HEADER" "true"
    print_styled "Dotfiles Deployment" "$HEADER" "true"
    print_styled "================================================\n" "$HEADER" "true"

    while IFS= read -r dotfile; do
        local rel_path="${dotfile#$dotfiles_dir/}"
        local dest_path="${home_dir}/${rel_path}"

        print_styled "Processing: ${rel_path}" "$OKBLUE"

        if [[ -f "$dotfile" ]]; then
            local src_content=$(<"$dotfile")

            if [[ -f "$dest_path" ]]; then
                # Backup existing file
                local backup_path="${backup_dir}/${rel_path}"
                mkdir -p "$(dirname "$backup_path")"
                cp "$dest_path" "$backup_path"
                print_styled "  $CHECK Backed up existing file" "$OKGREEN"

                # Read existing content
                local existing_content=$(<"$dest_path")

                # Check if custom tags already exist
                local start_tag_exists=$(grep -q "$CUSTOM_START_TAG" <<< "$existing_content" && echo true || echo false)
                local end_tag_exists=$(grep -q "$CUSTOM_END_TAG" <<< "$existing_content" && echo true || echo false)

                # Remove existing custom sections
                local cleaned_content=$(sed "/$CUSTOM_START_TAG/,/$CUSTOM_END_TAG/d" <<< "$existing_content")

                # Append new content, reusing existing tags if present
                {
                    echo "$cleaned_content"
                    [[ -n "$cleaned_content" && ! "$cleaned_content" =~ .*\\n$ ]] && echo
                    if [[ "$start_tag_exists" == "true" ]]; then
                        echo "$CUSTOM_START_TAG"
                    else
                        echo -e "\n$CUSTOM_START_TAG"
                    fi
                    echo "$src_content"
                    if [[ "$end_tag_exists" == "true" ]]; then
                        echo "$CUSTOM_END_TAG"
                    else
                        echo -e "$CUSTOM_END_TAG\n"
                    fi
                } > "$dest_path"
            else
                # Create new file with content and custom tags
                mkdir -p "$(dirname "$dest_path")"
                {
                    echo "$CUSTOM_START_TAG"
                    echo "$src_content"
                    echo -e "$CUSTOM_END_TAG\n"
                } > "$dest_path"
            fi

            print_styled "  $CHECK Added/updated content" "$OKGREEN"
            ((success_count++))
        else
            print_styled "  $CROSS Error: Source file not found" "$FAIL"
            ((fail_count++))
        fi

        echo  # Empty line for readability
    done < <(get_dotfiles_list "$dotfiles_dir")

    echo "$success_count $fail_count"
}

remove_custom_sections() {
    local content="$1"
    sed "/$CUSTOM_START_TAG/,/$CUSTOM_END_TAG/d" <<< "$content" | sed -e :a -e '/^\n*$/{$d;N;ba' -e '}'
}

update_repo_dotfiles() {
    local script_dir="$1"
    local home_dir="$2"
    shift 2
    local dotfiles=("$@")
    local dotfiles_dir="${script_dir}/dotfiles"

    print_styled "\n================================================" "$HEADER" "true"
    print_styled "Updating Dotfiles" "$HEADER" "true"
    print_styled "================================================\n" "$HEADER" "true"

    if [[ ${#dotfiles[@]} -eq 0 ]]; then
        mapfile -t dotfiles < <(find "$dotfiles_dir" -type f -printf '%P\n')
        print_styled "No specific dotfiles provided. Updating all dotfiles." "$WARNING"
    fi

    local updated_count=0
    local failed_count=0

    for dotfile in "${dotfiles[@]}"; do
        local src_path="${home_dir}/${dotfile}"
        local dest_path="${dotfiles_dir}/${dotfile}"

        if [[ -f "$src_path" ]]; then
            local content=$(<"$src_path")
            local custom_sections=$(extract_custom_sections "$content")

            if [[ -n "$custom_sections" ]]; then
                mkdir -p "$(dirname "$dest_path")"
                echo "$custom_sections" > "$dest_path"
                print_styled "$CHECK Updated $dotfile" "$OKGREEN"
                ((updated_count++))
            else
                print_styled "$CROSS No custom sections found in $dotfile" "$WARNING"
                ((failed_count++))
            fi
        else
            print_styled "$CROSS $dotfile not found in home directory" "$WARNING"
            ((failed_count++))
        fi
    done

    print_styled "\nUpdate Summary:" "$HEADER" "true"
    print_styled "$CHECK Successfully updated: $updated_count" "$OKGREEN"
    print_styled "$CROSS Failed to update: $failed_count" "$FAIL"
}

update_os_dotfiles() {
    local script_dir="$1"
    local home_dir="$2"
    local dotfiles_dir="${script_dir}/dotfiles"

    print_styled "\n================================================" "$HEADER" "true"
    print_styled "Updating OS Dotfiles" "$HEADER" "true"
    print_styled "================================================\n" "$HEADER" "true"

    local updated_count=0
    local failed_count=0

    while IFS= read -r dotfile; do
        local rel_path="${dotfile#$dotfiles_dir/}"
        local dest_path="${home_dir}/${rel_path}"

        print_styled "Updating: ${rel_path}" "$OKBLUE"

        if [[ -f "$dotfile" ]]; then
            mkdir -p "$(dirname "$dest_path")"
            if cp "$dotfile" "$dest_path"; then
                print_styled "  $CHECK Updated successfully" "$OKGREEN"
                ((updated_count++))
            else
                print_styled "  $CROSS Update failed" "$FAIL"
                ((failed_count++))
            fi
        else
            print_styled "  $CROSS Source file not found" "$WARNING"
            ((failed_count++))
        fi

        echo  # Empty line for readability
    done < <(get_dotfiles_list "$dotfiles_dir")

    print_styled "\nUpdate Summary:" "$HEADER" "true"
    print_styled "$CHECK Successfully updated: $updated_count" "$OKGREEN"
    if [[ $failed_count -gt 0 ]]; then
        print_styled "$CROSS Failed to update: $failed_count" "$FAIL"
    fi
}

cleanup_and_finalize() {
    print_styled "\n================================================" "$HEADER" "true"
    print_styled "Cleanup and Finalization" "$HEADER" "true"
    print_styled "================================================\n" "$HEADER" "true"

    # Set ZSH as the default shell
    print_styled "\n$ARROW Setting ZSH as the default shell..." "$OKBLUE"
    local zsh_paths="${APPLICATIONS[zsh,locations]}"
    local zsh_path=""
    for path in $zsh_paths; do
        if [[ -f "$path" ]]; then
            zsh_path="$path"
            break
        fi
    done

    if [[ -n "$zsh_path" ]]; then
        if chsh -s "$zsh_path"; then
            print_styled "  $CHECK ZSH set as default shell" "$OKGREEN"
        else
            print_styled "  $CROSS Failed to set ZSH as default" "$FAIL"
        fi
    else
        print_styled "  $CROSS ZSH not found in any of the expected locations" "$FAIL"
    fi

    # Clear and rebuild Homebrew cache
    print_styled "\n$ARROW Cleaning up Homebrew..." "$OKBLUE"
    if brew cleanup; then
        print_styled "  $CHECK Homebrew cleanup completed" "$OKGREEN"
    else
        print_styled "  $CROSS Homebrew cleanup failed" "$FAIL"
    fi

    # Verify installations
    print_styled "\n$ARROW Verifying installations..." "$OKBLUE"
    for app in "${!APPLICATIONS[@]}"; do
        IFS=',' read -r key field <<< "$app"
        if [[ "$field" == "name" ]]; then
            local name="${APPLICATIONS[$app]}"
            local locations="${APPLICATIONS[${key},locations]}"
            local installed=false

            for location in $locations; do
                if [[ -e "$location" ]]; then
                    print_styled "  $CHECK $name is installed" "$OKGREEN"
                    installed=true
                    break
                fi
            done

            if [[ "$installed" == "false" ]]; then
                print_styled "  $CROSS $name not found" "$FAIL"
            fi
        fi
    done

    # Finalization message
    print_styled "\n$ARROW Finalization complete" "$OKBLUE"
    print_styled "It's recommended to restart your system to ensure all changes take effect." "$WARNING"
}

clear_backups() {
    local script_dir="$1"
    local backup_dir="${script_dir}/backups"

    if [[ -d "$backup_dir" ]]; then
        if rm -rf "$backup_dir"; then
            print_styled "$CHECK Backups directory cleared successfully" "$OKGREEN"
        else
            print_styled "$CROSS Failed to clear backups" "$FAIL"
        fi
    else
        print_styled "No backups directory found" "$WARNING"
    fi
}

main() {
    print_header

    local script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
    local home_dir="$HOME"

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --clear)
                clear_backups "$script_dir"
                exit 0
                ;;
            --backup)
                backup_dotfiles "$script_dir" "$home_dir" "true"
                exit 0
                ;;
            --update_repo)
                shift
                local update_files=()
                while [[ $# -gt 0 && ! "$1" =~ ^-- ]]; do
                    update_files+=("$1")
                    shift
                done
                update_repo_dotfiles "$script_dir" "$home_dir" "${update_files[@]}"
                exit 0
                ;;
            --update_os)
                update_os_dotfiles "$script_dir" "$home_dir"
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                exit 1
                ;;
        esac
        shift
    done

    local backup_dir=$(create_backup_dir "$script_dir")

    print_styled "Starting Dotfiles and Software Installation" "$HEADER" "true" "true"

    # Backup existing dotfiles
    backup_dotfiles "$script_dir" "$home_dir"

    # Install software
    install_software "$script_dir"

    # Process dotfiles
    read success_count fail_count < <(process_dotfiles "$script_dir" "$home_dir" "$backup_dir")

    # Cleanup and finalize
    cleanup_and_finalize

    print_styled "\n================================================" "$HEADER" "true"
    print_styled "Installation Summary" "$HEADER" "true"
    print_styled "================================================" "$HEADER" "true"
    print_styled "$CHECK Successful dotfile operations: $success_count" "$OKGREEN" "true"
    if [[ $fail_count -gt 0 ]]; then
        print_styled "$CROSS Failed dotfile operations: $fail_count" "$FAIL" "true"
    fi
    print_styled "Backup directory: $backup_dir" "$WARNING"

    print_styled "\nInstallation process completed!" "$HEADER" "true"
    print_styled "Please review any error messages above and take necessary actions." "$WARNING"
    print_styled "It's recommended to restart your system to ensure all changes take effect." "$WARNING"

    # Ask user if they want to clear backups
    read -p $'\nDo you want to clear all backups? [y]es/[n]o: ' clear_backups_input
    clear_backups_input=$(echo "$clear_backups_input" | tr '[:upper:]' '[:lower:]')
    if [[ "$clear_backups_input" == "yes" || "$clear_backups_input" == "y" ]]; then
        clear_backups "$script_dir"
    else
        print_styled "You can clear the backups later by running:" "$WARNING"
        print_styled "./setup.sh --clear" "$OKBLUE"
    fi
}

# Clear the terminal screen
clear

# Run the main function
main "$@"