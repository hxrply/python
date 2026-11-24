# The whole thing on one page

*20. The whole thing on one page*

Every Task 4a solution has this shape. Swap the column names and the menu options. Numbers in comments = lesson numbers.

```python
import pandas as pd
import matplotlib.pyplot as plt

def load_data(file_name): ...            # 1
def clean_data(df): ...                  # 3
def add_income_profit(df): ...           # 9
def get_valid_number(prompt, lo, hi): ...# 5
def choose_category(df): ...             # 5
def get_date(prompt): ...                # 6
def get_date_range(): ...                # 6
def filter_dates(df, start, end): ...    # 6
def show_bar(...): ...                   # 14
def show_line(...): ...                  # 14

def category_report(df): ...    # option 1: choose -> filter -> totals -> table
def compare_categories(df): ... # option 2: groupby -> text -> bar chart
def income_trend(df): ...       # option 3: date range -> group by month -> line graph

def main(): ...                          # 16
main()
```
