#!/bin/bash

clear

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[0;37m'
ORANGE='\033[0;91m'
PURPLE='\033[0;94m'
NC='\033[0m' # No Color

# Symbols
CHECKMARK='\xE2\x9C\x94'
CROSS='\xE2\x9D\x8C'

# Directory for temporary backups
BACKUP_DIR=~/$(date +"%Y-%m-%d")_dotfile-backups

# Display header
echo -e "${CYAN}"
echo -e "███╗   ███╗ █████╗  ██████╗ ██████╗ ███████╗    ██████╗  ██████╗ ████████╗███████╗██╗██╗     ███████╗███████╗"
echo -e "████╗ ████║██╔══██╗██╔════╝██╔═══██╗██╔════╝    ██╔══██╗██╔═══██╗╚══██╔══╝██╔════╝██║██║     ██╔════╝██╔════╝"
echo -e "██╔████╔██║███████║██║     ██║   ██║███████╗    ██║  ██║██║   ██║   ██║   █████╗  ██║██║     █████╗  ███████╗"
echo -e "██║╚██╔╝██║██╔══██║██║     ██║   ██║╚════██║    ██║  ██║██║   ██║   ██║   ██╔══╝  ██║██║     ██╔══╝  ╚════██║"
echo -e "██║ ╚═╝ ██║██║  ██║╚██████╗╚██████╔╝███████║    ██████╔╝╚██████╔╝   ██║   ██║     ██║███████╗███████╗███████║"
echo -e "╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝    ╚═════╝  ╚═════╝    ╚═╝   ╚═╝     ╚═╝╚══════╝╚══════╝╚══════╝${NC}"
echo -e "\t${BLUE}by Henry Newcomer${NC}"
echo -e "${CYAN}=============================================================================================================${NC}\n"
echo

########
# .zshrc
########

SOURCE_FILE="zshrc"
ZSHRC_PATH=~/.zshrc
BACKUP_FILE=$(date +"%Y-%m-%d-%H-%M-%S").$SOURCE_FILE_backup


if [ ! -f $ZSHRC_PATH ]; then
    echo -e "${RED}${CROSS} Error: $ZSHRC_PATH not found. Aborting.${NC}"
    exit 1
fi

mkdir -p $BACKUP_DIR

cp $ZSHRC_PATH $BACKUP_DIR/$BACKUP_FILE
echo -e "${BLUE}Backup of $ZSHRC_PATH created at $BACKUP_DIR/$BACKUP_FILE ${CHECKMARK}${NC}"

REPO_SOURCE_PATH=$SOURCE_FILE

# Check if the source file exists in the repo
if [ ! -f $REPO_SOURCE_PATH ]; then
    echo -e "${RED}${CROSS} Error: $SOURCE_FILE not found in the repo. Aborting.${NC}"
    exit 1
fi

read -p "$(echo -e "${YELLOW}The contents of the repo's $SOURCE_FILE will be appended to your ${ZSHRC_PATH} file.\n${CYAN}Do you want to proceed? (y/n):${NC} ")" CONFIRM
if [ "$CONFIRM" != "y" ]; then
    echo -e "${YELLOW}${CROSS} Operation cancelled. No changes were made to $ZSHRC_PATH.${NC}"
    exit 0
fi

# Append contents of the repo's source file to the existing .zshrc
# Also add extra padding
echo -e "\n" >> $ZSHRC_PATH
cat $REPO_SOURCE_PATH >> $ZSHRC_PATH
echo -e "\n" >> $ZSHRC_PATH

echo -e "${GREEN}Contents of the repo's $SOURCE_FILE have been successfully appended to ${ZSHRC_PATH}. ${CHECKMARK}${NC}\n"

echo -e "${MAGENTA}Please manually verify that the changes to $ZSHRC_PATH occurred properly.${NC}\n"
read -p "$(echo -e "${BLUE}Would you like to remove the backup? ${CYAN}(y/n):${NC} ")" REMOVE_BACKUP

if [ "$REMOVE_BACKUP" == "y" ]; then
    # Remove the entire backup directory
    rm -rf $BACKUP_DIR
    echo -e "${BLUE}Backup directory has been removed. ${CHECKMARK}${NC}"
else
    echo -e "${BLUE}Backup is stored at $BACKUP_DIR ${CHECKMARK}${NC}"
fi

# EOF