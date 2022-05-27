from datetime import datetime
import json
from src import QueryList

query_list = QueryList()
now = str(datetime.utcnow())

with open("queries.json", "w") as f:
    json.dump({"executionTime": now, "queries": query_list.to_json()}, f, indent=4)

query_count = len(query_list)

for index, query in enumerate(query_list):
    print(
        f'({index+1}/{query_count}): ' +
        f'{query.t_from_int}-{query.t_to_int} ' +
        f'{query.sensor} {query.location} '
    )
    # gd.process_query.run(query)
