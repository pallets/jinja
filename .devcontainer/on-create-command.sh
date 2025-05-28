#!/bin/bash
set -e

# Install uv if not already installed
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Create venv using uv and install dependencies
echo "Creating virtual environment and installing dependencies..."
uv sync

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
pre-commit install --install-hooks
