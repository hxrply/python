# Comments, names and security

Code organisation (8) + Security (6) = 14 marks. None of it needs new pandas.

```python
# Comment WHY, not what:
#   bad:  # adds income
#   good: # income = quantity x sale price so we can compare categories by money, not units

# Names: snake_case verbs for functions, nouns for data
#   load_data, clean_data, get_valid_number, filter_dates, show_bar
#   df, drinks, start_date, by_category

# Security checklist:
#   - no global df: load in main(), pass df in, return results
#   - df = df.copy() before changing a filtered DataFrame
#   - try/except on every input and on loading, so no traceback is shown to the user
```

> One comment above every function: what it is for and what it returns.
