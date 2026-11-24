# The whole thing on one page

Every Task 4a solution has this shape. Swap the column names and the menu options. The "see 05" comments say which file explains that part.

```python
import pandas as pd
import matplotlib.pyplot as plt

def load_data(file_name): ...            # see 01
def clean_data(df): ...                  # see 03
def add_income_profit(df): ...           # see 09
def get_valid_number(prompt, lo, hi): ...# see 05
def choose_category(df): ...             # see 05
def get_date(prompt): ...                # see 06
def get_date_range(): ...                # see 06
def filter_dates(df, start, end): ...    # see 06
def show_bar(...): ...                   # see 13
def show_line(...): ...                  # see 13

def category_report(df): ...    # option 1: choose -> filter -> totals -> table
def compare_categories(df): ... # option 2: groupby -> text -> bar chart
def income_trend(df): ...       # option 3: date range -> group by month -> line graph

def main(): ...                          # see 15
main()
```
