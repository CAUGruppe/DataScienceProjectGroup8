import pandas as pd

df = pd.read_json("Data/Tagesschau_data_otherFormat.json")

keywords = ["israel", "gaza", "palestine", "hamas"]

mask = df["SOURCEURL"].str.contains("|".join(keywords), case=False, na=False)

df_filtered = df[mask]


print(df.columns)