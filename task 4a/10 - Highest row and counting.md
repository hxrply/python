# The highest row, and counting

*The row with the highest value*

`idxmax` finds where the biggest value is; `.loc` fetches that whole row.

```python
best_row = df.loc[df["Income"].idxmax()]          # the whole row
print(f"Best sale: {best_row['Product']} on {best_row['Date']:%d/%m/%Y}")

top5 = df.sort_values("Income", ascending=False).head(5)
```

```python
counts = df["Category"].value_counts()
print(counts)

drinks = counts.get("Drinks", 0)    # 0 if there are none
```

> In May `.get("Gold")` printed None. `.get("Gold", 0)` prints 0.
