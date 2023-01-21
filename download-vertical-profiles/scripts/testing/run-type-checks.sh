set -o errexit

echo "Running checks on run.py"
python -m mypy run.py
