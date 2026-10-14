#!/usr/bin/env bash
# Wrapper for make on Git Bash / Unix environments without make
if [ -f ".venv/bin/python" ]; then
    .venv/bin/python make.py "$@"
elif [ -f ".venv/Scripts/python.exe" ]; then
    .venv/Scripts/python.exe make.py "$@"
elif command -v python3 >/dev/null 2>&1; then
    python3 make.py "$@"
else
    python make.py "$@"
fi
