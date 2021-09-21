import json
import os

flags = {}

for filname in [f for f in os.listdir("data/json-out") if f.endswith(".json")]:
    with open(f"data/json-out/{filname}") as f:
        tss = json.load(f)["data"]["flagTimeseries"]
    for ts in tss:
        for flag in ts["data"]["ys"]:
            try:
                flags[flag] += 1
            except KeyError:
                flags[flag] = 1

print(
    json.dumps(
        {x: flags[x] for x in sorted(flags, key=(lambda x: flags[x]), reverse=True)},
        indent=2,
    )
)

# Relevant flags for hamburg: ['21', '8', '15', '33', '39', '37', '25', '24', '31']
