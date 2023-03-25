#!/bin/bash

# found at https://dirask.com/posts/Bash-get-current-script-directory-path-1X9E8D

# the automated-retrieval-pipeline directory
PROJECT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

"$PROJECT_DIR"/.venv/bin/python "$PROJECT_DIR"/src/cli/main.py "$@";
