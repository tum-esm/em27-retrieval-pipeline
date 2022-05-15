"""
Compare two json files and print their differences
"""

from deepdiff import DeepDiff
import json

with open("./data/json-out/20210419-old.json") as f:
    a = json.load(f)
with open("./data/json-out/20210419.json") as f:
    b = json.load(f)

difference = DeepDiff(a, b)

assert len(difference.keys()) == 0, difference
print("Files match!")
