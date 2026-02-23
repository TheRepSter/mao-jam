#!/bin/bash
rm *.log
rm *.json
# Remove pycache recursively from the current directory
find . -type d -name "__pycache__" -exec rm -fr {} +
rm Results.txt