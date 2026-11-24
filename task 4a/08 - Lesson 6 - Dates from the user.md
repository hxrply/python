# Dates from the user

*6. Dates from the user*

Keep asking until the date is real. Then check the start comes before the end.

```python
def get_date(prompt):
    while True:
        text = input(prompt + " (DD/MM/YYYY): ")
        try:
            return pd.to_datetime(text, format="%d/%m/%Y")
        except ValueError:
            print("That is not a valid date. Use DD/MM/YYYY, e.g. 05/10/2026.")

def get_date_range():
    while True:
        start = get_date("Start date")
        end = get_date("End date")
        if start <= end:
            return start, end
        print("The start date must be before the end date.")

def filter_dates(df, start, end):
    return df[(df["Date"] >= start) & (df["Date"] <= end)].copy()
```

> In May, get_date did `return True` on a bad date. It must loop and ask again.
