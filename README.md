# Henry's macOS Dotfiles

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This project provides a comprehensive solution for managing my dotfiles, installing software, and setting up a macOS environment. It allows you to easily deploy your dotfiles, update them, and install necessary software with a single command. The script is available in both Python and Bash versions for flexibility.

## Features

- Deploy dotfiles from a repository to your home directory
- Append custom sections to existing dotfiles or create new ones
- Update dotfiles in the repository from your home directory
- Install essential software using Homebrew
- Backup existing dotfiles before modification
- Clear backups when no longer needed
- Colorized and informative console output

## Prerequisites

- macOS operating system
- Internet connection for software installation

For Python version:
- Python 3.7 or higher

For Bash version:
- Bash shell (comes pre-installed on macOS)

## Installation

1. Clone this repository to your local machine:
   ```
   git clone https://github.com/HenryNewcomer/mac-dotfiles.git
   cd mac-dotfiles
   ```

2. Ensure the scripts have executable permissions:
   ```
   chmod +x setup.py setup.sh
   ```

## Usage

You can use either the Python or Bash version of the script:

### Python Version

1. Run the script directly:
   ```
   ./setup.py
   ```

2. Or use Python explicitly:
   ```
   python setup.py
   ```
   or
   ```
   python3 setup.py
   ```

### Bash Version

Run the script directly:
```
./setup.sh
```

Choose the version that works best for your system configuration.

### Deploy Dotfiles and Install Software

To deploy your dotfiles and install software:

Python: `./setup.py` or Bash: `./setup.sh`

This command will:
- Install Homebrew (if not already installed)
- Install specified software packages
- Deploy dotfiles from the `dotfiles` directory to your home directory
- Backup any existing dotfiles before modifying them
- Append custom sections to existing dotfiles or create new ones
- Set ZSH as the default shell (if installed)
- Perform cleanup tasks

### Update Dotfiles

To update specific dotfiles in the repository from your home directory:

Python: `./setup.py --update [file1] [file2] ...`
Bash: `./setup.sh --update [file1] [file2] ...`

For example:
```
./setup.py --update .zshrc .vimrc "config/kitty/kitty.conf"
```
or
```
./setup.sh --update .zshrc .vimrc "config/kitty/kitty.conf"
```

To update all dotfiles in the repository:

Python: `./setup.py --update`
Bash: `./setup.sh --update`

This will check for all files in the `dotfiles` directory and update them from your home directory. The update process will only modify the content between the custom tags in each file.

### Clear Backups

To clear all backup directories:

Python: `./setup.py --clear`
Bash: `./setup.sh --clear`

## Directory Structure

- `setup.py`: The main Python script
- `setup.sh`: The main Bash script
- `dotfiles/`: Directory containing your dotfiles
- `backups/`: Directory where backups are stored (created automatically)

## Customization

### Adding New Software

To add new software for installation, modify the `install_software` function in either `setup.py` or `setup.sh`. Add the package name to the list of applications to install or create a new installation function for more complex installations.

### Modifying Dotfiles

Place your dotfiles in the `dotfiles` directory, maintaining the same directory structure as in your home directory. For example:

```
dotfiles/
├── .zshrc
├── .vimrc
└── config/
    └── kitty/
        └── kitty.conf
```

Wrap your custom configurations in each dotfile with the following tags:

```
# >>> Henry's customizations
Your custom configurations here
# <<< Henry's customizations
```

You can have multiple custom sections in a single file, and they will all be preserved.

## How It Works

- When deploying dotfiles, the script will append the custom sections (content between the tags) to existing files in your home directory, or create new files if they don't exist.
- Custom sections are identified by the tags:
  - Start tag: `# >>> Henry's customizations`
  - End tag: `# <<< Henry's customizations`
- When updating dotfiles, the script will extract all custom sections from your home directory files and update the repository files with these sections.
- The script can handle multiple custom sections within a single dotfile.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

This means you are free to use, modify, distribute, and sell this software, as long as you include the original copyright notice and license terms. This software comes with no warranties or liabilities.

Note that this project may include or depend on third-party software that is licensed under different terms. Please refer to the license information of each dependency for more details.
