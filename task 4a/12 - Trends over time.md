# Trends over time

"Trends over time" is in every Task 4a brief. Group by day or month, then compare first and last.

```python
df["Month"] = df["Date"].dt.strftime("%Y-%m")       # 2026-09, 2026-10 ... sorts correctly
monthly = df.groupby("Month")["Income"].sum().round(2)

daily = df.groupby("Date")["Quantity"].sum()

first, last = monthly.iloc[0], monthly.iloc[-1]
change = (last - first) / first * 100
print(f"Income changed by {change:.1f}% from the first to the last month.")
```

> `%Y-%m` sorts in the right order (2026-09, 2026-10). Month names sort alphabetically - wrong.
