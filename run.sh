#!/bin/bash

# exit if any command fails
set -e

# pull latest changes from the repository
echo "pulling latest changes.."
git reset --hard -q HEAD
git pull -q origin main

# token check
if ! grep -q "^TOKEN=" .env 2>/dev/null; then
	echo "missing TOKEN in .env file"
	exit 1
fi

export TOKEN=$(cat "$TOKEN_FILE")

# install dependencies
echo "installing dependencies.."
python -m pip install -r req.txt -q

# run the bot
echo "waking up sem.."
python main.py