# Last 7, 14 or 30 days

*7. Last 7 / 14 / 30 days*

The mark scheme calls preset timeframes a higher-level answer. Count back from the newest date in the data.

Picture: the newest date in the data is the end; count back 7 days from it; everything older is left out.

```python
def last_n_days(df, n):
    latest = df["Date"].max()
    start = latest - pd.Timedelta(days=n - 1)
    return df[df["Date"] >= start].copy()

recent = last_n_days(df, 7)
```

> Use `df["Date"].max()`, not today - exam data can be months old.
