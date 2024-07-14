#!/usr/bin/env python3

import os
import shutil
import sys
import subprocess
import asyncio
import argparse
import re
import requests
import zipfile
import plistlib
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Callable, Dict
import xml.etree.ElementTree as ET

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
        'install_method': 'custom',
        'locations': ['/Applications/Kitty.app', '/opt/homebrew/bin/kitty']
    },
    'vim': {
        'name': 'Vim',
        'install_method': 'homebrew',
        'locations': ['/usr/bin/vim', '/opt/homebrew/bin/vim']
    },
    'nvim': {
        'name': 'Neovim',
        'install_method': 'homebrew',
        'locations': ['/usr/local/bin/nvim', '/opt/homebrew/bin/nvim']
    },
    'zsh': {
        'name': 'Zsh',
        'install_method': 'homebrew',
        'locations': ['/bin/zsh', '/usr/local/bin/zsh', '/opt/homebrew/bin/zsh']
    },
    'emacs': {
        'name': 'Emacs',
        'install_method': 'custom',
        'locations': ['/Applications/Emacs.app']
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
    """Install Kitty terminal emulator and set up the application bundle."""
    print_styled(f"\n{ARROW} Installing Kitty...", Colors.HEADER, bold=True)

    try:
        # Install Kitty using Homebrew
        returncode, _, stderr = await run_command(['brew', 'install', 'kitty'])
        if returncode != 0:
            raise Exception(f"Kitty installation failed: {stderr}")

        # Find the Kitty executable
        returncode, stdout, _ = await run_command(['which', 'kitty'])
        if returncode != 0:
            raise Exception("Kitty executable not found after installation")

        kitty_exec = stdout.strip()

        # Create the Applications directory if it doesn't exist
        applications_dir = Path("/Applications")
        applications_dir.mkdir(exist_ok=True)

        # Create the Kitty.app bundle
        kitty_app_path = applications_dir / "Kitty.app"
        if kitty_app_path.exists():
            shutil.rmtree(kitty_app_path)

        kitty_app_path.mkdir(parents=True)
        (kitty_app_path / "Contents" / "MacOS").mkdir(parents=True)

        # Create a launch script
        launch_script = kitty_app_path / "Contents" / "MacOS" / "kitty"
        with open(launch_script, 'w') as f:
            f.write(f"#!/bin/sh\nexec {kitty_exec} \"$@\"")
        launch_script.chmod(0o755)

        # Create the Info.plist file
        info_plist_path = kitty_app_path / "Contents" / "Info.plist"
        info_plist = {
            'CFBundleName': 'Kitty',
            'CFBundleDisplayName': 'Kitty',
            'CFBundleIdentifier': 'net.kovidgoyal.kitty',
            'CFBundleExecutable': 'kitty',
            'CFBundleIconFile': 'kitty.icns',
            'CFBundlePackageType': 'APPL',
        }
        with open(info_plist_path, 'wb') as f:
            plistlib.dump(info_plist, f)

        print_styled(f"{CHECK} Kitty installed successfully", Colors.OKGREEN)

        # Install custom Kitty icon
        await install_kitty_icon(script_dir, kitty_app_path)

    except Exception as e:
        print_styled(f"{CROSS} Kitty installation failed: {str(e)}", Colors.FAIL)

async def install_kitty_icon(script_dir: Path, kitty_app_path: Path) -> None:
    """Download and install custom Kitty icon."""
    print_styled(f"\n{ARROW} Installing custom Kitty icon...", Colors.HEADER, bold=True)
    downloads_dir = script_dir / "downloads" / "repos"
    downloads_dir.mkdir(parents=True, exist_ok=True)
    kitty_icon_zip = downloads_dir / "kitty-icon.zip"

    try:
        download_file(KITTY_ICON_REPO_URL, kitty_icon_zip)
        extract_zip(kitty_icon_zip, downloads_dir)
        kitty_icon_dir = next(downloads_dir.glob('kitty-icon-*'))  # Find the extracted directory

        icon_path = kitty_icon_dir / "build" / "neue_outrun.icns"
        if not icon_path.exists():
            raise FileNotFoundError("neue_outrun.icns not found in the downloaded repository")

        # Copy the new icon to Kitty.app
        dest_icon_path = kitty_app_path / "Contents" / "Resources" / "kitty.icns"
        dest_icon_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(icon_path, dest_icon_path)

        # Clear icon cache and restart Dock
        await run_command(['rm', '-rf', '/var/folders/*/*/*/com.apple.dock.iconcache'])
        await run_command(['killall', 'Dock'])

        print_styled(f"{CHECK} Custom Kitty icon installed successfully", Colors.OKGREEN)
    except Exception as e:
        print_styled(f"{CROSS} Custom Kitty icon installation failed: {str(e)}", Colors.FAIL)

async def install_emacs(script_dir: Path) -> None:
    """Download and install the latest version of Emacs."""
    print_styled(f"\n{ARROW} Installing Emacs...", Colors.HEADER, bold=True)

    # Check if Emacs is already installed
    emacs_app_path = Path("/Applications/Emacs.app")
    if emacs_app_path.exists():
        print_styled(f"{CHECK} Emacs is already installed. Skipping installation.", Colors.OKGREEN)
        print_styled(" >> Please check for updates manually. <<", Colors.ORANGE)
        return

    try:
        # Fetch the latest Emacs version from the RSS feed
        response = requests.get(EMACS_RSS_URL)
        response.raise_for_status()
        root = ET.fromstring(response.content)

        # Find the latest entry
        latest_entry = root.find('{http://www.w3.org/2005/Atom}entry')
        download_url = latest_entry.find('{http://www.w3.org/2005/Atom}link').get('href')
        version = latest_entry.find('{http://www.w3.org/2005/Atom}title').text

        # Download Emacs
        downloads_dir = script_dir / "downloads" / "emacs"
        downloads_dir.mkdir(parents=True, exist_ok=True)
        dmg_path = downloads_dir / f"Emacs-{version}.dmg"

        print_styled(f"Downloading Emacs {version}...", Colors.OKBLUE)
        download_file(download_url, dmg_path)

        # Mount the DMG
        print_styled("Mounting Emacs DMG...", Colors.OKBLUE)
        mount_process = await asyncio.create_subprocess_exec(
            'hdiutil', 'attach', str(dmg_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await mount_process.communicate()

        if mount_process.returncode != 0:
            raise Exception(f"Failed to mount DMG: {stderr.decode()}")

        # Copy Emacs.app to Applications
        print_styled("Installing Emacs...", Colors.OKBLUE)
        source_path = Path("/Volumes/Emacs/Emacs.app")
        shutil.copytree(source_path, emacs_app_path)

        # Unmount the DMG
        print_styled("Unmounting Emacs DMG...", Colors.OKBLUE)
        await run_command(['hdiutil', 'detach', '/Volumes/Emacs'])

        print_styled(f"{CHECK} Emacs {version} installed successfully", Colors.OKGREEN)
    except Exception as e:
        print_styled(f"{CROSS} Emacs installation failed: {str(e)}", Colors.FAIL)

async def install_software(script_dir: Path) -> None:
    """Install all required software."""
    if not await install_homebrew():
        print_styled("Homebrew installation failed. Skipping package installations.", Colors.FAIL)
        return

    await install_fira_code_font(script_dir)
    await install_kitty(script_dir)

    for app_key, app_info in APPLICATIONS.items():
        if app_key == 'kitty':
            continue  # Skip Kitty as it's handled separately
        if app_info['install_method'] == 'homebrew':
            if not await is_package_installed(app_key):
                await install_brew_package(app_key)
            else:
                print_styled(f"{CHECK} {app_info['name']} is already installed. Updating...", Colors.OKGREEN)
                await run_command(['brew', 'upgrade', app_key])
        elif app_info['install_method'] == 'custom' and app_key == 'emacs':
            await install_emacs(script_dir)

async def is_package_installed(package: str) -> bool:
    """Check if a package is already installed."""
    for location in APPLICATIONS[package]['locations']:
        if os.path.exists(location):
            return True
    return False

def extract_custom_sections(content: str) -> List[str]:
    """Extract all custom sections from the content."""
    pattern = re.compile(f"{CUSTOM_START_TAG}.*?{CUSTOM_END_TAG}", re.DOTALL)
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
                custom_sections = extract_custom_sections(src_file.read())

            if dest_path.exists():
                # Backup existing file
                backup_path = backup_dir / rel_path
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(dest_path), str(backup_path))
                print_styled(f"  {CHECK} Backed up existing file", Colors.OKGREEN)

                # Append custom sections
                with open(dest_path, 'a') as dest_file:
                    for section in custom_sections:
                        dest_file.write(f"\n\n{section}\n")
            else:
                # Create new file with custom sections
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                with open(dest_path, 'w') as dest_file:
                    for section in custom_sections:
                        dest_file.write(f"{section}\n\n")

            print_styled(f"  {CHECK} Added/updated custom content", Colors.OKGREEN)
            success_count += 1

        except Exception as e:
            print_styled(f"  {CROSS} Error: {str(e)}", Colors.FAIL)
            fail_count += 1

        print()  # Empty line for readability

    return success_count, fail_count

def update_dotfiles(script_dir: Path, home_dir: Path, dotfiles: List[str] = None) -> None:
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
        for location in app_info['locations']:
            if os.path.exists(location):
                print_styled(f"  {CHECK} {app_info['name']} is installed", Colors.OKGREEN)
                installed = True
                break
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

async def main(args: argparse.Namespace) -> None:
    """Main function to orchestrate the setup process."""
    print_header()

    script_dir = Path(__file__).parent.resolve()
    home_dir = Path.home()

    if args.clear:
        clear_backups(script_dir)
        return

    if args.backup:
        backup_dotfiles(script_dir, home_dir, standalone=True)
        return

    if args.update is not None:
        update_dotfiles(script_dir, home_dir, args.update)
        return

    backup_dir = create_backup_dir(script_dir)

    print_styled("Starting Dotfiles and Software Installation", Colors.HEADER, bold=True, underline=True)

    # Backup existing dotfiles
    backup_dotfiles(script_dir, home_dir)

    # Install software
    await install_software(script_dir)

    # Process dotfiles
    success_count, fail_count = process_dotfiles(script_dir, home_dir, backup_dir)

    # Cleanup and finalize
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
        print_styled(f"./setup.py --clear", Colors.OKBLUE)

def get_args():
    parser = argparse.ArgumentParser(description="Dotfiles and software installation script")
    parser.add_argument("--clear", action="store_true", help="Clear all backups and exit")
    parser.add_argument("--update", nargs='*', help="Update specified dotfiles in the repository, or all if none specified")
    parser.add_argument("--backup", action="store_true", help="Perform a standalone backup of dotfiles")
    return parser.parse_args()

if __name__ == "__main__":
    os.system('clear') # Clear the terminal screen (Unix/Linux)
    args = get_args()
    asyncio.run(main(args))
