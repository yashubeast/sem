#!/bin/bash

# exit if any command fails
set -e

# pull latest changes from the repository
git pull origin main

# install dependencies
echo "Installing dependencies.."
python -m pip install -r req.txt

# function for token
if [ ! -f .env ] || ! grep -q "^TOKEN=" .env; then

	# prompt for token
	read -p "Enter your bot token: " TOKEN

	# save to .env
	echo "TOKEN=$TOKEN" > .env
fi

# run the bot
echo "Waking up sem.."
python main.py