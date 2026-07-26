#!/bin/bash
CHANGED_FILES=$(git show --name-only --format="" HEAD | grep -E "^(src|code)/")
echo "$CHANGED_FILES"
