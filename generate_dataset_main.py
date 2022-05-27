import json

from rich.progress import track
from src import generate_dataset as gd


query_list = gd.generate_query_list.run()

with open("queries.json", "w") as f:
    json.dump(query_list, f, indent=4)

print(f"{len(query_list)} queries")
for query in track(query_list):
    gd.process_query.run(query)
