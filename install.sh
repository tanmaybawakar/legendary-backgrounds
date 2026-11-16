#!/bin/sh
# Compatibility entry point; setup.py also works on Windows.
set -e
if [ "$#" -eq 0 ]; then set -- claude; fi
exec python3 "$(dirname "$0")/setup.py" "$@"
