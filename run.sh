#!/bin/bash

# exit if any command fails
set -e

# pull latest changes from the repository
git reset --hard HEAD
git pull origin main

# token check
if ! grep -q "^TOKEN=" .env 2>/dev/null; then
	echo "missing TOKEN in .env file"
	exit 1
fi

# install dependencies
echo "Installing dependencies.."
python -m pip install -r req.txt -q

# run the bot
echo "Waking up sem.."
python main.py