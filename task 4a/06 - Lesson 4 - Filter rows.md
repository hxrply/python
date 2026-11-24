# Keep only the rows you want

*4. Pick columns and filter rows*

Filtering is how you answer "show me X". Each test goes in its own brackets.

```python
drinks = df[df["Category"] == "Drinks"]                                  # one condition
big_drinks = df[(df["Category"] == "Drinks") & (df["Quantity"] > 10)]     # AND
food = df[(df["Category"] == "Snacks") | (df["Category"] == "Hot Food")]  # OR
food = df[df["Category"].isin(["Snacks", "Hot Food"])]                    # same, shorter
small = df[["Date", "Product", "Quantity"]]                               # only some columns

def filter_category(df, category):
    result = df[df["Category"] == category].copy()
    return result
```

> Use `&` and `|`, never the words and / or. Missing brackets gives "truth value of a Series is ambiguous".
