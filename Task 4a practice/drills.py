# Task 4a practice drills - Pixel Cafe sales (cafe_sales.csv, same folder)
# Do ONE drill at a time. Fill in the function, run the file, send me what happened.
# Each drill is 2-10 lines. Together they build a full Task 4a solution.

import pandas as pd
import matplotlib.pyplot as plt


# ---------------------------------------------------------------
# Drill 1 - load the CSV ONCE, without crashing if it is missing
# ---------------------------------------------------------------
def load_data(file_name):
    # TODO(human): read file_name into a DataFrame and return it.
    # If the file does not exist, print a friendly message and return None
    # instead of crashing.
    pass


# ---------------------------------------------------------------
# Drill 2 - clean the data (do after Drill 1)
# ---------------------------------------------------------------
def clean_data(df):
    pass


# ---------------------------------------------------------------
# Drill 3 - filter one category (do after Drill 2)
# ---------------------------------------------------------------
def filter_category(df, category):
    pass


# ---------------------------------------------------------------
# Drill 4 - ask for a date until it is valid (do after Drill 3)
# ---------------------------------------------------------------
def get_date(prompt):
    pass


# ---------------------------------------------------------------
# Drill 5 - income and profit (do after Drill 4)
# ---------------------------------------------------------------
def add_income_profit(df):
    pass


# ---------------------------------------------------------------
# Drill 6 - compare every category with groupby (do after Drill 5)
# ---------------------------------------------------------------
def totals_by_category(df):
    pass


# ---------------------------------------------------------------
# Drill 7 - graphs (do after Drill 6)
# ---------------------------------------------------------------
def show_bar(totals):
    pass


# ---------------------------------------------------------------
# Drill 8 - last N days (do after Drill 7)
# ---------------------------------------------------------------
def last_n_days(df, n):
    pass


# ---------------------------------------------------------------
# Test area - runs when you press Run
# ---------------------------------------------------------------
data = load_data("cafe_sales.csv")
print(data.head() if data is not None else "No data loaded")

missing = load_data("not_a_real_file.csv")
print("Missing file returned:", missing)
