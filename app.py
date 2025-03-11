#!/usr/bin/env python3

import argparse
import asyncio
import os
import plistlib
import re
import requests
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, time
from pathlib import Path
from typing import List, Tuple, Callable, Dict

# ANSI color codes for styled output
class Colors:
    HEADER    = '\033[95m'
    OKBLUE    = '\033[94m'
    OKGREEN   = '\033[92m'
    WARNING   = '\033[93m'
    ORANGE    = '\033[38;5;208m'
    FAIL      = '\033[91m'
    ENDC      = '\033[0m'
    BOLD      = '\033[1m'
    UNDERLINE = '\033[4m'
    CYAN      = '\033[96m'

# Symbols for visual indicators
CHECK = '✓'
CROSS = '✗'
ARROW = '→'

# Custom tags for dotfiles
CUSTOM_START_TAG = "# >>> Henry's customizations"
CUSTOM_END_TAG   = "# <<< Henry's customizations"

# URLs for downloads
FIRA_CODE_URL       = "https://github.com/tonsky/FiraCode/releases/download/6.2/Fira_Code_v6.2.zip"
KITTY_ICON_REPO_URL = "https://github.com/k0nserv/kitty-icon/archive/refs/heads/master.zip"
EMACS_RSS_URL       = "https://emacsformacosx.com/atom/release"

# Global mapping of applications to install
APPLICATIONS = {
    'kitty': {
        'name': 'Kitty',
        'install_method': 'homebrew',
        'package': 'kitty',  # The actual homebrew package name
        'locations': [  # Optional - if not provided, just checks if brew has it installed
            '/Applications/kitty.app',
            '/opt/homebrew/bin/kitty'
        ],
        'post_install': ['install_kitty_icon'],  # Additional functions to run after installation
    },
    'vim': {
        'name': 'Vim',
        'install_method': 'homebrew',
        'package': 'vim'
    },
    'nvim': {
        'name': 'Neovim',
        'install_method': 'homebrew',
        'package': 'neovim'
    },
    'zsh': {
        'name': 'Zsh',
        'install_method': 'homebrew',
        'package': 'zsh',
        'locations': [
            '/bin/zsh',
            '/usr/local/bin/zsh',
            '/opt/homebrew/bin/zsh'
        ]
    },
    'emacs': {
        'name': 'Emacs',
        'install_method': 'homebrew',
        'package': 'emacs',
        'cask': True,
        'locations': ['/Applications/Emacs.app']
        # Original method:
        # 'install_method': 'custom',
        # 'install_function': 'install_emacs',
        # 'locations': ['/Applications/Emacs.app']
    },
    'tree': {
        'name': 'Tree',
        'install_method': 'homebrew',
        'install_function': 'tree'
    }
}

def print_styled(text: str, color: str, bold: bool = False, underline: bool = False) -> None:
    """Print styled text to the console."""
    style = color
    if bold:
        style += Colors.BOLD
    if underline:
        style += Colors.UNDERLINE
    print(f"{style}{text}{Colors.ENDC}")

def print_header():
    """Print the stylized header."""
    header = f"""
{Colors.CYAN}
███╗   ███╗ █████╗  ██████╗ ██████╗ ███████╗    ██████╗  ██████╗ ████████╗███████╗██╗██╗     ███████╗███████╗
████╗ ████║██╔══██╗██╔════╝██╔═══██╗██╔════╝    ██╔══██╗██╔═══██╗╚══██╔══╝██╔════╝██║██║     ██╔════╝██╔════╝
██╔████╔██║███████║██║     ██║   ██║███████╗    ██║  ██║██║   ██║   ██║   █████╗  ██║██║     █████╗  ███████╗
██║╚██╔╝██║██╔══██║██║     ██║   ██║╚════██║    ██║  ██║██║   ██║   ██║   ██╔══╝  ██║██║     ██╔══╝  ╚════██║
██║ ╚═╝ ██║██║  ██║╚██████╗╚██████╔╝███████║    ██████╔╝╚██████╔╝   ██║   ██║     ██║███████╗███████╗███████║
╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝    ╚═════╝  ╚═════╝    ╚═╝   ╚═╝     ╚═╝╚══════╝╚══════╝╚══════╝
{Colors.ENDC}
\t{Colors.OKBLUE}by Henry Newcomer{Colors.ENDC}
{Colors.CYAN}=============================================================================================================
{Colors.ENDC}
"""
    print(header)

def create_backup_dir(script_dir: Path, standalone: bool = False) -> Path:
    """Create a timestamped backup directory."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if standalone:
        backup_dir = script_dir / "backups" / "_standalones" / timestamp
    else:
        backup_dir = script_dir / "backups" / timestamp
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir

async def run_command(cmd: List[str]) -> Tuple[int, str, str]:
    """Run a shell command asynchronously and return its output."""
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    return process.returncode, stdout.decode(), stderr.decode()

def download_file(url: str, destination: Path) -> None:
    """Download a file from a URL to a specified destination."""
    response = requests.get(url)
    response.raise_for_status()
    with open(destination, 'wb') as f:
        f.write(response.content)

def extract_zip(zip_path: Path, extract_to: Path) -> None:
    """Extract a zip file to a specified directory."""
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

async def install_homebrew() -> bool:
    """Install or update Homebrew package manager."""
    print_styled(f"\n{ARROW} Checking Homebrew installation...", Colors.HEADER, bold=True)

    # Check if Homebrew is already installed
    returncode, stdout, _ = await run_command(['which', 'brew'])

    if returncode == 0:
        print_styled(f"{CHECK} Homebrew is already installed. Updating...", Colors.OKGREEN)
        update_cmd = ['brew', 'update']
    else:
        print_styled("Homebrew not found. Installing...", Colors.WARNING)
        install_script = '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
        update_cmd = ['/bin/bash', '-c', install_script]

    print_styled("This may take a few minutes. Please enter your password if prompted.", Colors.WARNING)

    process = await asyncio.create_subprocess_exec(
        *update_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT
    )

    while True:
        line = await process.stdout.readline()
        if not line:
            break
        print(line.decode().strip())

    await process.wait()

    if process.returncode == 0:
        print_styled(f"{CHECK} Homebrew {'updated' if returncode == 0 else 'installed'} successfully", Colors.OKGREEN)
        return True
    else:
        print_styled(f"{CROSS} Homebrew {'update' if returncode == 0 else 'installation'} failed", Colors.FAIL)
        return False

async def install_brew_package(package: str) -> None:
    """Install a package using Homebrew."""
    print_styled(f"{ARROW} Installing {package}...", Colors.OKBLUE)
    returncode, _, stderr = await run_command(['brew', 'install', package])
    if returncode == 0:
        print_styled(f"{CHECK} {package} installed successfully", Colors.OKGREEN)
    else:
        print_styled(f"{CROSS} {package} installation failed: {stderr}", Colors.FAIL)

async def install_fira_code_font(script_dir: Path) -> None:
    """Download and install Fira Code font."""
    print_styled(f"\n{ARROW} Installing Fira Code font...", Colors.HEADER, bold=True)
    downloads_dir = script_dir / "downloads" / "other"
    downloads_dir.mkdir(parents=True, exist_ok=True)
    font_zip = downloads_dir / "FiraCode.zip"
    font_dir = Path.home() / "Library" / "Fonts"

    try:
        download_file(FIRA_CODE_URL, font_zip)
        extract_zip(font_zip, font_dir)
        print_styled(f"{CHECK} Fira Code font installed successfully", Colors.OKGREEN)
    except Exception as e:
        print_styled(f"{CROSS} Fira Code font installation failed: {str(e)}", Colors.FAIL)

async def install_kitty(script_dir: Path) -> None:
    """Install Kitty terminal emulator using Homebrew."""
    print_styled(f"\n{ARROW} Installing Kitty...", Colors.HEADER, bold=True)

    try:
        # Check if Kitty is already installed
        returncode, _, _ = await run_command(['brew', 'list', 'kitty'])
        if returncode == 0:
            print_styled(f"{CHECK} Kitty is already installed. Updating...", Colors.OKGREEN)
            cmd = ['brew', 'upgrade', 'kitty']
        else:
            print_styled("Installing Kitty...", Colors.OKBLUE)
            cmd = ['brew', 'install', 'kitty']

        # Install or update Kitty
        returncode, stdout, stderr = await run_command(cmd)
        if returncode != 0:
            raise Exception(f"Kitty installation failed: {stderr}")

        print_styled(f"{CHECK} Kitty installed successfully", Colors.OKGREEN)

        # Install the custom icon
        await install_kitty_icon(script_dir)

    except Exception as e:
        print_styled(f"{CROSS} Kitty installation failed: {str(e)}", Colors.FAIL)

async def install_kitty_icon(script_dir: Path) -> None:
    """Download and install custom Kitty icon."""
    print_styled(f"\n{ARROW} Installing custom Kitty icon...", Colors.HEADER, bold=True)
    downloads_dir = script_dir / "downloads" / "repos"
    downloads_dir.mkdir(parents=True, exist_ok=True)
    kitty_icon_zip = downloads_dir / "kitty-icon.zip"

    try:
        # Download and extract the kitty-icon repository
        download_file(KITTY_ICON_REPO_URL, kitty_icon_zip)
        extract_zip(kitty_icon_zip, downloads_dir)
        kitty_icon_dir = next(downloads_dir.glob('kitty-icon-*'))  # Find the extracted directory

        # Find the desired icon (e.g., 'neue_outrun.icns')
        icon_path = kitty_icon_dir / "build" / "neue_outrun.icns"
        if not icon_path.exists():
            raise FileNotFoundError("neue_outrun.icns not found in the downloaded repository")

        # Determine Kitty config directory
        kitty_config_dir = Path.home() / ".config" / "kitty"
        kitty_config_dir.mkdir(parents=True, exist_ok=True)

        # Copy the icon to the Kitty config directory
        dest_icon_path = kitty_config_dir / "kitty.app.icns"
        shutil.copy2(icon_path, dest_icon_path)

        print_styled(f"{CHECK} Custom Kitty icon installed successfully", Colors.OKGREEN)
        print_styled("The icon will be applied automatically when Kitty starts.", Colors.OKBLUE)
        print_styled("You may need to restart Kitty for the changes to take effect.", Colors.WARNING)

        # Clear icon cache and restart Dock
        await run_command(['rm', '-rf', '/var/folders/*/*/*/com.apple.dock.iconcache'])
        await run_command(['killall', 'Dock'])

    except Exception as e:
        print_styled(f"{CROSS} Custom Kitty icon installation failed: {str(e)}", Colors.FAIL)

async def install_emacs(script_dir: Path) -> None:
    """Install Emacs Plus 30 using Homebrew and ensure it's discoverable."""
    print_styled(f"\n{ARROW} Installing Emacs Plus 30...", Colors.HEADER, bold=True)

    try:
        # Tap the emacs-plus repository
        print_styled("Tapping emacs-plus repository...", Colors.OKBLUE)
        await run_command(['brew', 'tap', 'd12frosted/emacs-plus'])

        # Install Emacs Plus 30
        print_styled("Installing Emacs Plus 30...", Colors.OKBLUE)
        install_cmd = [
            'brew', 'install', 'emacs-plus@30',
            '--with-xwidgets',
            '--with-imagemagick',
            '--with-modern-icon'
        ]

        process = await asyncio.create_subprocess_exec(
            *install_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )

        while True:
            line = await process.stdout.readline()
            if not line:
                break
            print(line.decode().strip())

        await process.wait()

        if process.returncode == 0:
            print_styled(f"{CHECK} Emacs Plus 30 installed successfully", Colors.OKGREEN)

            # Remove existing Emacs.app
            print_styled("Removing existing Emacs.app from Applications...", Colors.OKBLUE)
            await run_command(['sudo', 'rm', '-rf', '/Applications/Emacs.app'])

            # Copy Emacs.app to Applications
            print_styled("Copying Emacs.app to Applications folder...", Colors.OKBLUE)
            await run_command(['sudo', 'cp', '-R', '/opt/homebrew/opt/emacs-plus@30/Emacs.app', '/Applications/'])

            # Change ownership
            print_styled("Changing ownership of Emacs.app...", Colors.OKBLUE)
            await run_command(['sudo', 'chown', '-R', f'{os.getlogin()}:staff', '/Applications/Emacs.app'])

            # Force Spotlight to reindex Applications
            print_styled("Forcing Spotlight to reindex Applications...", Colors.OKBLUE)
            await run_command(['sudo', 'mdutil', '-E', '/Applications'])

            print_styled(f"{CHECK} Emacs should now be discoverable by Spotlight", Colors.OKGREEN)

            # Restart Alfred
            print_styled("Restarting Alfred to recognize the new Emacs installation...", Colors.OKBLUE)
            try:
                # Quit Alfred
                subprocess.run(['osascript', '-e', 'tell application "Alfred 5" to quit'])
                time.sleep(2)  # Wait for Alfred to fully quit

                # Start Alfred
                subprocess.run(['open', '-a', 'Alfred 5'])
                time.sleep(2)  # Wait for Alfred to start

                print_styled(f"{CHECK} Alfred has been restarted", Colors.OKGREEN)
                print_styled("Emacs should now be discoverable in Alfred. If not, please try rebuilding Alfred's cache manually.", Colors.WARNING)
            except Exception as e:
                print_styled(f"{CROSS} Failed to restart Alfred: {str(e)}", Colors.WARNING)
                print_styled("Please restart Alfred manually to recognize the new Emacs installation.", Colors.WARNING)

        else:
            raise Exception("Emacs Plus 30 installation failed")

    except Exception as e:
        print_styled(f"{CROSS} Emacs Plus 30 installation failed: {str(e)}", Colors.FAIL)

async def install_software(script_dir: Path) -> None:
    """Install all required software using the improved configuration system."""
    if not await install_homebrew():
        print_styled("Homebrew installation failed. Skipping package installations.", Colors.FAIL)
        return

    await install_fira_code_font(script_dir)

    for app_key, app_info in APPLICATIONS.items():
        if await is_package_installed(app_key):
            print_styled(f"{CHECK} {app_info['name']} is already installed. Updating...", Colors.OKGREEN)
            if app_info['install_method'] == 'homebrew':
                # Use the package_key as the homebrew package name if not specified otherwise
                package_name = app_info.get('package', app_key)

                # Check if this is a cask installation
                upgrade_cmd = ['brew', 'upgrade']
                if app_info.get('cask', False):
                    upgrade_cmd.append('--cask')
                upgrade_cmd.append(package_name)

                await run_command(upgrade_cmd)
            continue

        if app_info['install_method'] == 'homebrew':
            print_styled(f"{ARROW} Installing {app_info['name']}...", Colors.OKBLUE)
            # Use the package_key as the homebrew package name if not specified otherwise
            package_name = app_info.get('package', app_key)

            # Check if this is a cask installation
            install_cmd = ['brew', 'install']
            if app_info.get('cask', False):
                install_cmd.append('--cask')
            install_cmd.append(package_name)

            returncode, _, stderr = await run_command(install_cmd)

            if returncode == 0:
                print_styled(f"{CHECK} {app_info['name']} installed successfully", Colors.OKGREEN)

                # Run any post-install functions
                if 'post_install' in app_info:
                    for func_name in app_info['post_install']:
                        if func_name in globals():
                            await globals()[func_name](script_dir)
            else:
                print_styled(f"{CROSS} {app_info['name']} installation failed: {stderr}", Colors.FAIL)

        elif app_info['install_method'] == 'custom':
            if 'install_function' in app_info and app_info['install_function'] in globals():
                await globals()[app_info['install_function']](script_dir)
            else:
                print_styled(f"{CROSS} No installation function found for {app_info['name']}", Colors.FAIL)

    print()  # Add an extra blank line after software installation

async def check_brew_package(package: str) -> bool:
    """Check if a package is installed via Homebrew."""
    returncode, _, _ = await run_command(['brew', 'list', package])
    return returncode == 0

async def is_package_installed(package_key: str) -> bool:
    """Check if a package is installed using the most appropriate method."""
    package_info = APPLICATIONS[package_key]

    # If locations are specified, check those first
    if 'locations' in package_info and package_info['locations']:
        if any(os.path.exists(location) for location in package_info['locations']):
            return True

    # For homebrew packages, also check brew list
    if package_info['install_method'] == 'homebrew':
        # Use the package_key as the homebrew package name if not specified otherwise
        package_name = package_info.get('package', package_key)
        return await check_brew_package(package_name)

    return False

def extract_custom_sections(content: str) -> List[str]:
    """Extract all custom sections from the content, including tags."""
    pattern = re.compile(f"({re.escape(CUSTOM_START_TAG)}.*?{re.escape(CUSTOM_END_TAG)})", re.DOTALL)
    return pattern.findall(content)

def get_dotfiles_list(dotfiles_dir: Path) -> List[Path]:
    """Get a list of all dotfiles in the repository."""
    return [f for f in dotfiles_dir.rglob('*') if f.is_file()]

def backup_dotfiles(script_dir: Path, home_dir: Path, standalone: bool = False) -> Tuple[int, int]:
    """Backup dotfiles from the home directory to the backup directory."""
    dotfiles_dir = script_dir / "dotfiles"
    backup_dir = create_backup_dir(script_dir, standalone)

    print_styled(f"\n{'='*50}", Colors.HEADER, bold=True)
    print_styled("Backing up Dotfiles", Colors.HEADER, bold=True)
    print_styled(f"{'='*50}\n", Colors.HEADER, bold=True)

    success_count = 0
    fail_count = 0

    for dotfile in get_dotfiles_list(dotfiles_dir):
        rel_path = dotfile.relative_to(dotfiles_dir)
        src_path = home_dir / rel_path
        dest_path = backup_dir / rel_path

        print_styled(f"Backing up: {rel_path}", Colors.OKBLUE)

        try:
            if src_path.exists():
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, dest_path)
                print_styled(f"  {CHECK} Backed up successfully", Colors.OKGREEN)
                success_count += 1
            else:
                print_styled(f"  {CROSS} Source file not found", Colors.WARNING)
                fail_count += 1
        except Exception as e:
            print_styled(f"  {CROSS} Backup failed: {str(e)}", Colors.FAIL)
            fail_count += 1

        print()  # Empty line for readability

    print_styled(f"\nBackup Summary:", Colors.HEADER, bold=True)
    print_styled(f"{CHECK} Successfully backed up: {success_count}", Colors.OKGREEN)
    if fail_count > 0:
        print_styled(f"{CROSS} Failed to back up: {fail_count}", Colors.FAIL)
    print_styled(f"Backup directory: {backup_dir}", Colors.WARNING)

    return success_count, fail_count

def process_dotfiles(script_dir: Path, home_dir: Path, backup_dir: Path) -> Tuple[int, int]:
    """Process and deploy dotfiles."""
    success_count = 0
    fail_count = 0

    print_styled(f"\n{'='*50}", Colors.HEADER, bold=True)
    print_styled("Dotfiles Deployment", Colors.HEADER, bold=True)
    print_styled(f"{'='*50}\n", Colors.HEADER, bold=True)

    dotfiles_dir = script_dir / "dotfiles"
    for dotfile in get_dotfiles_list(dotfiles_dir):
        rel_path = dotfile.relative_to(dotfiles_dir)
        dest_path = home_dir / rel_path

        print_styled(f"Processing: {rel_path}", Colors.OKBLUE)

        try:
            with open(dotfile, 'r') as src_file:
                src_content = src_file.read()

            if dest_path.exists():
                # Backup existing file
                backup_path = backup_dir / rel_path
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(dest_path), str(backup_path))
                print_styled(f"  {CHECK} Backed up existing file", Colors.OKGREEN)

                # Read existing content
                with open(dest_path, 'r') as dest_file:
                    existing_content = dest_file.read()

                # Extract existing custom sections
                existing_sections = extract_custom_sections(existing_content)

                # Remove empty or misplaced custom sections
                cleaned_sections = [section for section in existing_sections if section.strip() != f"{CUSTOM_START_TAG}\n{CUSTOM_END_TAG}"]

                # Prepare new content
                new_content = remove_custom_sections(existing_content)
                if new_content and not new_content.endswith('\n'):
                    new_content += '\n'

                # Append cleaned existing sections and new content
                new_content += '\n'.join(cleaned_sections)
                if cleaned_sections:
                    new_content += '\n'
                new_content += f"{CUSTOM_START_TAG}\n{src_content.strip()}\n{CUSTOM_END_TAG}\n"

                # Write updated content
                with open(dest_path, 'w') as dest_file:
                    dest_file.write(new_content)

            else:
                # Create new file with content and custom tags
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                with open(dest_path, 'w') as dest_file:
                    dest_file.write(f"{CUSTOM_START_TAG}\n{src_content.strip()}\n{CUSTOM_END_TAG}\n")

            print_styled(f"  {CHECK} Added/updated content", Colors.OKGREEN)
            success_count += 1

        except Exception as e:
            print_styled(f"  {CROSS} Error: {str(e)}", Colors.FAIL)
            fail_count += 1

        print()  # Empty line for readability

    return success_count, fail_count

def remove_custom_sections(content: str) -> str:
    """Remove all custom sections from the content."""
    pattern = re.compile(f"{re.escape(CUSTOM_START_TAG)}.*?{re.escape(CUSTOM_END_TAG)}\n?", re.DOTALL)
    return pattern.sub('', content).strip()

def update_os_dotfiles(script_dir: Path, home_dir: Path) -> None:
    """Update OS dotfiles from the repository."""
    dotfiles_dir = script_dir / "dotfiles"

    print_styled(f"\n{'='*50}", Colors.HEADER, bold=True)
    print_styled("Updating OS Dotfiles", Colors.HEADER, bold=True)
    print_styled(f"{'='*50}\n", Colors.HEADER, bold=True)

    updated_count = 0
    failed_count = 0

    for dotfile in get_dotfiles_list(dotfiles_dir):
        rel_path = dotfile.relative_to(dotfiles_dir)
        dest_path = home_dir / rel_path

        print_styled(f"Updating: {rel_path}", Colors.OKBLUE)

        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dotfile, dest_path)
            print_styled(f"  {CHECK} Updated successfully", Colors.OKGREEN)
            updated_count += 1
        except Exception as e:
            print_styled(f"  {CROSS} Update failed: {str(e)}", Colors.FAIL)
            failed_count += 1

        print()  # Empty line for readability

    print_styled(f"\nUpdate Summary:", Colors.HEADER, bold=True)
    print_styled(f"{CHECK} Successfully updated: {updated_count}", Colors.OKGREEN)
    if failed_count > 0:
        print_styled(f"{CROSS} Failed to update: {failed_count}", Colors.FAIL)

def update_repo_dotfiles(script_dir: Path, home_dir: Path, dotfiles: List[str] = None) -> None:
    """Update specified dotfiles in the repository from the home directory."""
    dotfiles_dir = script_dir / "dotfiles"

    print_styled(f"\n{'='*50}", Colors.HEADER, bold=True)
    print_styled("Updating Dotfiles", Colors.HEADER, bold=True)
    print_styled(f"{'='*50}\n", Colors.HEADER, bold=True)

    if dotfiles is None or len(dotfiles) == 0:
        dotfiles = [str(f.relative_to(dotfiles_dir)) for f in get_dotfiles_list(dotfiles_dir)]
        print_styled("No specific dotfiles provided. Updating all dotfiles.", Colors.WARNING)

    updated_count = 0
    failed_count = 0

    for dotfile in dotfiles:
        src_path = home_dir / dotfile
        dest_path = dotfiles_dir / dotfile

        if src_path.exists():
            try:
                with open(src_path, 'r') as src_file:
                    content = src_file.read()
                    custom_sections = extract_custom_sections(content)

                    if custom_sections:
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(dest_path, 'w') as dest_file:
                            dest_file.write('\n\n'.join(custom_sections))
                        print_styled(f"{CHECK} Updated {dotfile}", Colors.OKGREEN)
                        updated_count += 1
                    else:
                        print_styled(f"{CROSS} No custom sections found in {dotfile}", Colors.WARNING)
                        failed_count += 1
            except Exception as e:
                print_styled(f"{CROSS} Failed to update {dotfile}: {str(e)}", Colors.FAIL)
                failed_count += 1
        else:
            print_styled(f"{CROSS} {dotfile} not found in home directory", Colors.WARNING)
            failed_count += 1

    print_styled(f"\nUpdate Summary:", Colors.HEADER, bold=True)
    print_styled(f"{CHECK} Successfully updated: {updated_count}", Colors.OKGREEN)
    print_styled(f"{CROSS} Failed to update: {failed_count}", Colors.FAIL)

async def cleanup_and_finalize() -> None:
    """Perform cleanup tasks and finalize the installation."""
    print_styled(f"\n{'='*50}", Colors.HEADER, bold=True)
    print_styled("Cleanup and Finalization", Colors.HEADER, bold=True)
    print_styled(f"{'='*50}\n", Colors.HEADER, bold=True)

    # Set ZSH as the default shell
    print_styled(f"\n{ARROW} Setting ZSH as the default shell...", Colors.OKBLUE)
    if 'locations' in APPLICATIONS['zsh']:
        zsh_paths = APPLICATIONS['zsh']['locations']
        zsh_path = next((path for path in zsh_paths if os.path.exists(path)), None)

        if zsh_path:
            try:
                subprocess.run(['chsh', '-s', zsh_path])
                print_styled(f"  {CHECK} ZSH set as default shell", Colors.OKGREEN)
            except Exception as e:
                print_styled(f"  {CROSS} Failed to set ZSH as default: {str(e)}", Colors.FAIL)
        else:
            print_styled(f"  {CROSS} ZSH not found in any of the expected locations", Colors.FAIL)
    else:
        print_styled(f"  {CROSS} No ZSH locations configured", Colors.WARNING)

    # Clear and rebuild Homebrew cache
    print_styled(f"\n{ARROW} Cleaning up Homebrew...", Colors.OKBLUE)
    try:
        await run_command(['brew', 'cleanup'])
        print_styled(f"  {CHECK} Homebrew cleanup completed", Colors.OKGREEN)
    except Exception as e:
        print_styled(f"  {CROSS} Homebrew cleanup failed: {str(e)}", Colors.FAIL)

    # Verify installations
    print_styled(f"\n{ARROW} Verifying installations...", Colors.OKBLUE)
    for app_key, app_info in APPLICATIONS.items():
        installed = False

        # Check specific locations if defined
        if 'locations' in app_info and app_info['locations']:
            for location in app_info['locations']:
                if os.path.exists(location):
                    print_styled(f"  {CHECK} {app_info['name']} is installed (found at {location})", Colors.OKGREEN)
                    installed = True
                    break

        # For homebrew packages, also check brew list
        if not installed and app_info['install_method'] == 'homebrew':
            # Use the package_key as the homebrew package name if not specified otherwise
            package_name = app_info.get('package', app_key)
            returncode, _, _ = await run_command(['brew', 'list', package_name])
            if returncode == 0:
                print_styled(f"  {CHECK} {app_info['name']} is installed via Homebrew", Colors.OKGREEN)
                installed = True

        if not installed:
            print_styled(f"  {CROSS} {app_info['name']} not found", Colors.FAIL)

    # Finalization message
    print_styled(f"\n{ARROW} Finalization complete", Colors.OKBLUE)
    print_styled("It's recommended to restart your system to ensure all changes take effect.", Colors.WARNING)

def clear_backups(script_dir: Path) -> None:
    """Clear all backup directories."""
    backup_dir = script_dir / "backups"

    if backup_dir.exists():
        try:
            shutil.rmtree(backup_dir)
            print_styled(f"{CHECK} Backups directory cleared successfully", Colors.OKGREEN)
        except Exception as e:
            print_styled(f"{CROSS} Failed to clear backups: {str(e)}", Colors.FAIL)
    else:
        print_styled("No backups directory found", Colors.WARNING)

async def display_menu() -> int:
    """Display an interactive menu and return the user's choice."""
    menu_options = {
        1: "Update OS dotfiles from repository TO the OS(most common)",
        2: "Backup existing OS dotfiles",
        3: "Update repository dotfiles FROM the OS",
        4: "Run FULL installation (software + dotfiles)",
        5: "Clear all backups",
        6: "Exit"
    }

    print_styled("\nPlease select an option:", Colors.HEADER, bold=True)
    for key, value in menu_options.items():
        if key == 1:  # Highlight the most common option
            print_styled(f"{key}. {value} {Colors.BOLD}(recommended){Colors.ENDC}", Colors.OKGREEN)
        else:
            print_styled(f"{key}. {value}", Colors.OKBLUE)

    while True:
        try:
            choice = int(input("\nEnter your choice (1-6): "))
            if 1 <= choice <= 6:
                return choice
            print_styled("Please enter a number between 1 and 6", Colors.WARNING)
        except ValueError:
            print_styled("Please enter a valid number", Colors.WARNING)


async def main(args: argparse.Namespace) -> None:
    """Main function to orchestrate the setup process."""
    print_header()

    script_dir = Path(__file__).parent.resolve()
    home_dir = Path.home()

    # If command-line arguments are provided, use them
    if any([args.update_os, args.backup, args.clear, args.update_repo is not None]):
        if args.clear:
            clear_backups(script_dir)
            return
        if args.backup:
            backup_dotfiles(script_dir, home_dir, standalone=True)
            return
        if args.update_repo is not None:
            update_repo_dotfiles(script_dir, home_dir, args.update_repo)
            return
        if args.update_os:
            update_os_dotfiles(script_dir, home_dir)
            return
    else:
        # If no arguments, show interactive menu
        choice = await display_menu()

        if choice == 1:
            update_os_dotfiles(script_dir, home_dir)
            return
        elif choice == 2:
            backup_dotfiles(script_dir, home_dir, standalone=True)
            return
        elif choice == 3:
            update_repo_dotfiles(script_dir, home_dir, None)  # None means update all
            return
        elif choice == 4:  # Full installation
            backup_dir = create_backup_dir(script_dir)
            print_styled("Starting Dotfiles and Software Installation", Colors.HEADER, bold=True, underline=True)
            backup_dotfiles(script_dir, home_dir)
            await install_software(script_dir)
            success_count, fail_count = process_dotfiles(script_dir, home_dir, backup_dir)
            await cleanup_and_finalize()

            print_styled(f"\n{'='*50}", Colors.HEADER, bold=True)
            print_styled("Installation Summary", Colors.HEADER, bold=True)
            print_styled(f"{'='*50}", Colors.HEADER, bold=True)
            print_styled(f"{CHECK} Successful dotfile operations: {success_count}", Colors.OKGREEN, bold=True)
            if fail_count > 0:
                print_styled(f"{CROSS} Failed dotfile operations: {fail_count}", Colors.FAIL, bold=True)
            print_styled(f"Backup directory: {backup_dir}", Colors.WARNING)
            print_styled("\nInstallation process completed!", Colors.HEADER, bold=True)
            print_styled("Please review any error messages above and take necessary actions.", Colors.WARNING)
            print_styled("It's recommended to restart your system to ensure all changes take effect.", Colors.WARNING)

            # Ask user if they want to clear backups
            clear_backups_input = input("\nDo you want to clear all backups? [y]es/[n]o: ").lower()
            if clear_backups_input == 'yes' or clear_backups_input == 'y':
                clear_backups(script_dir)
            else:
                print_styled("You can clear the backups later by running:", Colors.WARNING)
                print_styled(f"./app.py --clear", Colors.OKBLUE)

        elif choice == 5:  # Clear backups
            clear_backups(script_dir)
            return
        elif choice == 6:  # Exit
            print_styled("Exiting...", Colors.OKBLUE)
            return

def get_args():
    parser = argparse.ArgumentParser(description="Dotfiles and software installation script")
    parser.add_argument("--backup", action="store_true", help="Perform a standalone backup of existing OS dotfiles")
    parser.add_argument("--clear", action="store_true", help="Clear all backups")
    parser.add_argument("--update_repo", nargs='*', help="Update specified dotfiles in the repository (from the OS), or ALL if none specified")
    parser.add_argument("--update_os", action="store_true", help="Update OS dotfiles from the repository")
    return parser.parse_args()

if __name__ == "__main__":
    os.system('clear') # Clear the terminal screen (Unix/Linux)
    args = get_args()
    asyncio.run(main(args))
