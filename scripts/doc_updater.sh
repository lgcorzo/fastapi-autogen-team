#!/bin/bash

# Extract changed files in src/ or code/ using git diff vs HEAD~1 or fallback
if git rev-parse HEAD~1 >/dev/null 2>&1; then
    CHANGED_FILES=$(git diff HEAD~1 --name-only | grep -E "^(src|code)/")
else
    CHANGED_FILES=$(git show --name-only --format="" HEAD | grep -E "^(src|code)/")
fi

if [ -n "$CHANGED_FILES" ]; then
    python3 scripts/doc_updater.py $CHANGED_FILES
else
    echo "No relevant files modified."
fi
