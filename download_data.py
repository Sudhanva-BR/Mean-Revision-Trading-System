
import yfinance as yf
import os

os.makedirs("data", exist_ok=True)

df = yf.download(
    "RELIANCE.NS",
    period="5y",
    interval="1d",
    auto_adjust=False
)

if df.empty:
    raise RuntimeError("No stock data downloaded")

# Flatten columns if Yahoo returns multi-level columns
if hasattr(df.columns, "levels"):
    df.columns = df.columns.get_level_values(0)

df.to_csv("data/RELIANCE.csv")

print("Download successful!")
print("Total records:", len(df))
print(df.head())
