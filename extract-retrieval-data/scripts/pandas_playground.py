import pandas as pd

df = pd.DataFrame(columns=["a", "b"], data=[[1, 323], [2, 300], [3, 1]])

df.loc[df["a"] < df["b"], "a"] /= 300

print(df)
