set -o errexit

echo "Removing old mypy cache"
rm -rf .mypy_cache 

echo "Running checks on run_retrieval.py"
python -m mypy run_retrieval.py

echo "Running checks on print_processing_queue.py"
python -m mypy print_processing_queue.py

echo "Running checks on tests/pylot"
python -m mypy tests/pylot
