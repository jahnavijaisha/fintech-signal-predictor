import pandas as pd

path = "data/raw/confirmed_cfo_departures.csv"
df = pd.read_csv(path, dtype=str)

before = len(df)
df_clean = df.drop_duplicates(keep="first")
after = len(df_clean)

print(f"Rows before: {before}")
print(f"Rows after:  {after}")
print(f"Dropped:     {before - after}")

df_clean.to_csv(path, index=False)
print(f"\nSaved cleaned file back to {path}")