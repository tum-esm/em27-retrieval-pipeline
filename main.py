from datetime import datetime
import json
from src.utils import load_setup
from src import QueryList, QueryProcess

PROJECT_DIR, CONFIG = load_setup(validate=True)

query_list = QueryList()
now = str(datetime.utcnow())
query_count = len(query_list)

failed_queries = []

if query_count == 0:
    print("nothing to process")

for index, query in enumerate(query_list):
    print(
        f'({index+1}/{query_count}): ' +
        f'{query.t_from_int}-{query.t_to_int} ' +
        f'{query.sensor} {query.location} '
    )
    process = QueryProcess(query)
    if not process.was_successful():
        failed_queries.append(query.to_json())

report_name = datetime.utcnow().strftime("execution-summary-%Y%m%d-%H%M-UTC")

with open(f"reports/{report_name}.json", "w") as f:
    json.dump({
        "executionTime": now,
        "query_count": query_count,
        "failed_queries": failed_queries,
        "queries": query_list.to_json()
    }, f, indent=4)
