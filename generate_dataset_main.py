import json

from rich.progress import track
from src import generate_dataset as gd


query_list = gd.generate_query_list.run()

print(json.dumps(query_list, indent=4))
print(len(query_list))

for query in track(query_list):
    print(query)
    gd.process_query.run(query)
