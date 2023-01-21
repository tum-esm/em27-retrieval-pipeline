set -o errexit

echo "Running checks on run_retrieval.py"
python -m mypy run_retrieval.py
