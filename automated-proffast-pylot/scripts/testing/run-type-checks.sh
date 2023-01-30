set -o errexit

echo "Running checks on run_retrieval.py"
python -m mypy run_retrieval.py

echo "Running checks on print_processing_queue.py"
python -m mypy print_processing_queue.py

echo "Running checks on print_processing_queue.py"
python -m mypy tests/pylot
