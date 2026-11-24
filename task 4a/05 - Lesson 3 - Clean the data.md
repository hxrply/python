# Clear the glitched items first

*3. Clean the data*

A CSV is all text, and exam data has junk: blanks, "two", -3. Convert first, then bin the bad rows.

```python
def clean_data(df):
    df = df.copy()
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")   # junk -> NaN
    df["Cost Price"] = pd.to_numeric(df["Cost Price"], errors="coerce")
    df["Sale Price"] = pd.to_numeric(df["Sale Price"], errors="coerce")
    df = df.dropna()                       # remove rows with any empty value
    df = df[df["Quantity"] > 0]            # remove impossible values
    df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y")
    return df
```

> **Order matters:** `to_numeric` turns junk into NaN, then `dropna` removes the NaN.
