# One line for every number

*Totals, averages, highest and lowest*

Always round money to 2 dp and put words around the number.

| You want | Write |
|---|---|
| Total | `df["Quantity"].sum()` |
| Average | `df["Quantity"].mean()` |
| Highest / lowest | `.max()` / `.min()` |
| How many rows | `len(df)` |
| Money to 2 dp | `f"£{total:.2f}"` → £1234.50 |
| With commas | `f"£{total:,.2f}"` → £1,234.50 |


```python
total = df["Quantity"].sum()
average = df["Quantity"].mean()
highest = df["Quantity"].max()
lowest = df["Quantity"].min()
rows = len(df)

print(f"Total sold: {total} items in {rows} sales")
print(f"Average per sale: {average:.2f} items")    # 2 decimal places
print(f"Total income: £{1234.5:,.2f}")             # £1,234.50 - commas + 2 dp
```

> Not "1234.5" on its own - "Total income for Drinks in October: £1,234.50".
