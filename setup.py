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
from typing import List, Tuple, Callable

# ANSI color codes for styled output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    CYAN = '\033[96m'

# Symbols for visual indicators
CHECK = '✓'
CROSS = '✗'
ARROW = '→'

# Custom tags for dotfiles
CUSTOM_START_TAG = "# >>> Henry's customizations"
CUSTOM_END_TAG = "# <<< Henry's customizations"

# URLs for downloads
FIRA_CODE_URL = "https://github.com/tonsky/FiraCode/releases/download/6.2/Fira_Code_v6.2.zip"
KITTY_ICON_REPO_URL = "https://github.com/k0nserv/kitty-icon/archive/refs/heads/master.zip"

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

async def install_kitty_icon(script_dir: Path) -> None:
    """Download and install custom Kitty icon."""
    print_styled(f"\n{ARROW} Installing custom Kitty icon...", Colors.HEADER, bold=True)
    downloads_dir = script_dir / "downloads" / "repos"
    downloads_dir.mkdir(parents=True, exist_ok=True)
    kitty_icon_zip = downloads_dir / "kitty-icon.zip"
    kitty_icon_dir = downloads_dir / "kitty-icon"

    try:
        kitty_app_path = Path("/Applications/kitty.app")
        if not kitty_app_path.exists():
            print_styled(f"{CROSS} Kitty.app not found in /Applications. Skipping icon installation.", Colors.WARNING)
            return

        download_file(KITTY_ICON_REPO_URL, kitty_icon_zip)
        extract_zip(kitty_icon_zip, downloads_dir)
        kitty_icon_dir = next(downloads_dir.glob('kitty-icon-*'))  # Find the extracted directory

        icon_path = kitty_icon_dir / "build" / "neue_outrun.icns"
        if not icon_path.exists():
            raise FileNotFoundError("neue_outrun.icns not found in the downloaded repository")

        # Update Kitty.app icon
        info_plist_path = kitty_app_path / "Contents" / "Info.plist"

        # Check if we have permission to modify the Info.plist file
        if not os.access(str(info_plist_path), os.W_OK):
            print_styled(f"{CROSS} Permission denied to modify Kitty.app. Please run the script with sudo.", Colors.FAIL)
            return

        with open(info_plist_path, 'rb') as f:
            info_plist = plistlib.load(f)

        info_plist['CFBundleIconFile'] = 'neue_outrun.icns'

        with open(info_plist_path, 'wb') as f:
            plistlib.dump(info_plist, f)

        # Copy the new icon to Kitty.app
        shutil.copy2(icon_path, kitty_app_path / "Contents" / "Resources" / "neue_outrun.icns")

        # Clear icon cache and restart Dock
        await run_command(['rm', '-rf', '/var/folders/*/*/*/com.apple.dock.iconcache'])
        await run_command(['killall', 'Dock'])

        print_styled(f"{CHECK} Custom Kitty icon installed successfully", Colors.OKGREEN)
    except Exception as e:
        print_styled(f"{CROSS} Custom Kitty icon installation failed: {str(e)}", Colors.FAIL)
        print_styled("You may need to run the script with sudo or grant permissions to modify /Applications", Colors.WARNING)

async def install_software(script_dir: Path) -> None:
    """Install all required software."""
    brew_packages = ['kitty', 'emacs', 'vim', 'neovim', 'zsh']

    if not await install_homebrew():
        print_styled("Homebrew installation failed. Skipping package installations.", Colors.FAIL)
        return

    await install_fira_code_font(script_dir)
    await install_kitty_icon(script_dir)

    for package in brew_packages:
        if await is_package_installed(package):
            print_styled(f"{CHECK} {package} is already installed. Updating...", Colors.OKGREEN)
            await run_command(['brew', 'upgrade', package])
        else:
            await install_brew_package(package)

async def is_package_installed(package: str) -> bool:
    """Check if a package is already installed."""
    returncode, _, _ = await run_command(['brew', 'list', package])
    return returncode == 0

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
    zsh_path = '/usr/local/bin/zsh'
    try:
        if os.path.exists(zsh_path):
            subprocess.run(['chsh', '-s', zsh_path])
            print_styled(f"  {CHECK} ZSH set as default shell", Colors.OKGREEN)
        else:
            print_styled(f"  {CROSS} ZSH not found at {zsh_path}", Colors.FAIL)
    except Exception as e:
        print_styled(f"  {CROSS} Failed to set ZSH as default: {str(e)}", Colors.FAIL)

    # Clear and rebuild Homebrew cache
    print_styled(f"\n{ARROW} Cleaning up Homebrew...", Colors.OKBLUE)
    try:
        await run_command(['brew', 'cleanup'])
        print_styled(f"  {CHECK} Homebrew cleanup completed", Colors.OKGREEN)
    except Exception as e:
        print_styled(f"  {CROSS} Homebrew cleanup failed: {str(e)}", Colors.FAIL)

    # Verify installations
    print_styled(f"\n{ARROW} Verifying installations...", Colors.OKBLUE)
    for package in ['kitty', 'emacs', 'vim', 'neovim', 'zsh']:
        try:
            result = await run_command(['which', package])
            if result[0] == 0:
                print_styled(f"  {CHECK} {package} is installed", Colors.OKGREEN)
            else:
                print_styled(f"  {CROSS} {package} not found", Colors.FAIL)
        except Exception as e:
            print_styled(f"  {CROSS} Failed to verify {package}: {str(e)}", Colors.FAIL)

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
    print_styled(f"{CROSS} Failed dotfile operations: {fail_count}", Colors.FAIL, bold=True)
    print_styled(f"Backup directory: {backup_dir}", Colors.WARNING)

    print_styled("\nInstallation process completed!", Colors.HEADER, bold=True)
    print_styled("Please review any error messages above and take necessary actions.", Colors.WARNING)
    print_styled("It's recommended to restart your system to ensure all changes take effect.", Colors.WARNING)

    # Ask user if they want to clear backups
    clear_backups_input = input("\nDo you want to clear all backups? (yes/no): ").lower()
    if clear_backups_input == 'yes':
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
