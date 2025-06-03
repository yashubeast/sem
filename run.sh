#!/bin/bash

# exit if any command fails
set -e

# pull latest changes from the repository
git pull origin main

# install dependencies
echo "Installing dependencies.."
python -m pip install -r req.txt

# run the bot
echo "Waking up sem.."
python main.py