#!/bin/bash

# Directory to clean (default = current directory)
DIR="${1:-.}"

# Number of files to keep
KEEP=10

cd "$DIR" || { echo "Failed to access directory"; exit 1; }

# List files sorted by newest first, skip first $KEEP, delete the rest
ls -1t | tail -n +$((KEEP + 1)) | while read -r file; do
    echo "Deleting: $file"
    rm -f -- "$file"
done