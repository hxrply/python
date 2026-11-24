# Income and profit for every row

*9. New columns: income and profit*

One line works out a value for every row at once - no loop.

| Qty | Sale | Cost | Income (new) | Profit (new) |
|---|---|---|---|---|
| 5 | 2.20 | 0.80 | 11.00 | 7.00 |
| 8 | 1.50 | 0.25 | 12.00 | 10.00 |
| 3 | 3.50 | 1.10 | 10.50 | 7.20 |


```python
def add_income_profit(df):
    df = df.copy()
    df["Income"] = df["Quantity"] * df["Sale Price"]
    df["Profit"] = df["Quantity"] * (df["Sale Price"] - df["Cost Price"])
    return df

df = add_income_profit(df)
print(f"Total profit: £{df['Profit'].sum():.2f}")
```

> Income = quantity × sale price. Profit = quantity × (sale - cost).
