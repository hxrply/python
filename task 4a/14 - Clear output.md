# Output that makes sense

*Output that makes sense to the user*

Words around every number. No index column. A heading that says what and when.

```python
print("\n--- Drinks sales, 01/10/2026 to 31/10/2026 ---")
print(result[["Date", "Product", "Quantity"]].to_string(index=False))

if result.empty:
    print("No sales found for those dates.")
```

> Check `result.empty` first - the mean of nothing is NaN, and its graph is blank.
