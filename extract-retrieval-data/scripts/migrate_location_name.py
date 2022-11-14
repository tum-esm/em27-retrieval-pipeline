import json
import os

for f in os.listdir("data/json-out"):
    if f.endswith(".json"):
        print(f, end="")
        with open(f"data/json-out/{f}", "r") as fileobject:
            o = json.load(fileobject)
        modified = False
        for i in range(len(o)):
            if o[i]["location"] == "GR\u00c4":
                o[i]["location"] = "GRAE"
                modified = True
        if modified:
            print(" M")
            with open(f"data/json-out/{f}", "w") as fileobject:
                json.dump(o, fileobject, indent=4)
        else:
            print()
