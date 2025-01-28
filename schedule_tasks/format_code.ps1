#!/usr/bin/env pwsh

# Format code with Black (line length 79 as per PEP 8)
python -m black . -l 79

# Sort imports with isort (line length 79)
python -m isort . --line-length 79

# Lint and fix with Ruff (line length 79)
python -m ruff check . --fix --line-length 79
