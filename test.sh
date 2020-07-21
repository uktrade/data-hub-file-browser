#!/bin/bash -e
echo "Running Flake8 linter..."
flake8
echo "Running Pytest..."
pytest dhfb
