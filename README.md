# Henry's macOS Dotfiles

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This script provides a comprehensive solution for managing my dotfiles, installing software, and setting up a macOS environment. It allows you to easily deploy your dotfiles, update them, and install necessary software with a single command.

## Features

- Deploy dotfiles from a repository to your home directory
- Append custom sections to existing dotfiles or create new ones
- Update dotfiles in the repository from your home directory
- Install essential software using Homebrew
- Backup existing dotfiles before modification
- Clear backups when no longer needed
- Colorized and informative console output

## Prerequisites

- Python 3.7 or higher
- macOS operating system
- Internet connection for software installation

## Installation

1. Clone this repository to your local machine:
   ```
   git clone https://github.com/yourusername/macos-dotfiles-manager.git
   cd macos-dotfiles-manager
   ```

2. Ensure the script has executable permissions:
   ```
   chmod +x setup.py
   ```

## Usage

You can run the script in two ways:

1. Directly (make sure the script is executable):
   ```
   ./setup.py
   ```

2. Using Python:
   ```
   python setup.py
   ```
   or
   ```
   python3 setup.py
   ```

Choose the method that works best for your system configuration.

### Deploy Dotfiles and Install Software

To deploy your dotfiles and install software:

```
./setup.py
```

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

```
./setup.py --update [file1] [file2] ...
```

For example:
```
./setup.py --update .zshrc .vimrc "config/kitty/kitty.conf"
```

To update all dotfiles in the repository:

```
./setup.py --update
```

This will check for all files in the `dotfiles` directory and update them from your home directory. The update process will only modify the content between the custom tags in each file.

### Clear Backups

To clear all backup directories:

```
./setup.py --clear
```

## Directory Structure

- `setup.py`: The main script
- `dotfiles/`: Directory containing your dotfiles
- `backups/`: Directory where backups are stored (created automatically)

## Customization

### Adding New Software

To add new software for installation, modify the `install_software` function in `setup.py`. Add the package name to the `brew_packages` list or create a new installation function for more complex installations.

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
