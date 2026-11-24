# Compare every group in one line

*12. Compare groups with groupby*

"Compare all categories" is a higher-level answer in the mark scheme. groupby = split, then add up.

Picture: **all rows** (Drinks 3.00, Snacks 1.50, Drinks 4.40, Hot Food 7.00 ...) → **split by Category** (Drinks: 3.00 + 4.40) → **add up each** (Drinks 7.40, Snacks 3.50, Hot Food 10.50).

```python
by_category = df.groupby("Category")["Income"].sum().round(2)
by_category = by_category.sort_values(ascending=False)
print(by_category)

for category, income in by_category.items():
    print(f"{category}: £{income:.2f}")
```

> Read it as: split by Category -> take Income -> add up each group.
