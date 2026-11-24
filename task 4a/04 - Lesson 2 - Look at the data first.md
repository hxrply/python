# Check the map before the mission

*2. Look at the data before you write anything*

Five minutes at the start saves an hour of KeyErrors. `object` = text. `int64` / `float64` = numbers.

What `df.dtypes` prints for the cafe data:

```
Date          object
Product ID    object
Product       object
Category      object
Quantity      object   <- text! junk inside ("two", "abc")
Cost Price    float64
Sale Price    float64
```


```python
print(df.head())          # first 5 rows
print(df.columns)         # exact column names (spelling, spaces, capitals)
print(df.dtypes)          # object = text, int64/float64 = numbers
print(df.shape)           # (rows, columns)
print(df["Category"].unique())   # every different value in a column
```

> Copy column names from `df.columns` - in May the flight CSV header was spelt "Desination".
