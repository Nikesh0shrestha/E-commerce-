import pandas as pd

# Load JSON files from raw folder
ratings = pd.read_json("raw/ratings.json")
products = pd.read_json("raw/products.json")
users = pd.read_json("raw/users.json")

# Save CSV files into processed folder
ratings.to_csv("processed/ratings.csv", index=False)
products.to_csv("processed/products.csv", index=False)
users.to_csv("processed/users.csv", index=False)

print("✅ Conversion completed!")