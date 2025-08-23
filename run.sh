#!/bin/bash

# exit if any command fails
set -e

# token check
if [ -z "$TOKEN" ]; then
  echo "missing TOKEN in .env file"
  exit 1
fi

# run the bot
echo "waking up sem.."
python main.py