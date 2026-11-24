# Task 4a - pandas guide

Everything you need for Task 4a, in the order you build it. Examples use the Pixel Cafe data (cafe_sales.csv: Date, Product ID, Product, Category, Quantity, Cost Price, Sale Price). In the exam, swap in the column names from the CSV you are given.

Work through it with Claude one lesson at a time. Practice data: `cafe_sales.csv`. Drills: `drills.py`.

## Where the 34 marks are

| Area | Marks | What gets them |
|---|---|---|
| Code organisation | 8 | Load once, pass df into functions, clear names, comments that say WHY |
| User experience | 8 | Numbered menus, helpful messages, money to 2 dp, a titled and labelled graph |
| Functionality | 6 | It runs and the answers are right |
| Security | 6 | No global df, .copy() inside functions, try/except so no tracebacks are shown |
| Logic | 3 | Menu loops until Exit, conditions are right |
| Robustness | 3 | Bad input never crashes it: letters, out of range, bad dates, start after end, no results |

## Contents

- [1. Import and load the CSV once](#1-import-and-load-the-csv-once)
- [2. Look at the data before you write anything](#2-look-at-the-data-before-you-write-anything)
- [3. Clean the data](#3-clean-the-data)
- [4. Pick columns and filter rows](#4-pick-columns-and-filter-rows)
- [5. A numbered menu built FROM the data](#5-a-numbered-menu-built-from-the-data)
- [6. Dates from the user](#6-dates-from-the-user)
- [7. Last 7 / 14 / 30 days](#7-last-7--14--30-days)
- [8. Totals, averages, highest and lowest](#8-totals-averages-highest-and-lowest)
- [9. New columns: income and profit](#9-new-columns-income-and-profit)
- [10. The row with the highest value](#10-the-row-with-the-highest-value)
- [11. Counting things](#11-counting-things)
- [12. Compare groups with groupby](#12-compare-groups-with-groupby)
- [13. Trends over time](#13-trends-over-time)
- [14. Graphs](#14-graphs)
- [15. Output that makes sense to the user](#15-output-that-makes-sense-to-the-user)
- [16. The main menu loop](#16-the-main-menu-loop)
- [17. Using the code you are given](#17-using-the-code-you-are-given)
- [18. Comments, names and security](#18-comments-names-and-security)
- [19. Errors you will probably see](#19-errors-you-will-probably-see)
- [20. The whole thing on one page](#20-the-whole-thing-on-one-page)

## 1. Import and load the CSV once

Load the file ONCE and pass df into every other function. If the file is missing, show a message instead of crashing.

```python
import pandas as pd
import matplotlib.pyplot as plt

def load_data(file_name):
    try:
        df = pd.read_csv(file_name)
        return df
    except FileNotFoundError:
        print(f"Could not find {file_name}. Put it in the same folder as this program.")
        return None
```

> In except, df was never made - so return None, not df.

## 2. Look at the data before you write anything

Spend 5 minutes on this at the start of the exam. Wrong column names cause most KeyErrors.

```python
print(df.head())          # first 5 rows
print(df.columns)         # exact column names (spelling, spaces, capitals)
print(df.dtypes)          # object = text, int64/float64 = numbers
print(df.shape)           # (rows, columns)
print(df["Category"].unique())   # every different value in a column
```

> Copy column names from df.columns - in May the flight CSV header was spelt "Desination".

## 3. Clean the data

Everything in a CSV starts as text, and exam data has junk in it. Convert, then drop the bad rows.

```python
def clean_data(df):
    df = df.copy()
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")   # junk -> NaN
    df["Cost Price"] = pd.to_numeric(df["Cost Price"], errors="coerce")
    df["Sale Price"] = pd.to_numeric(df["Sale Price"], errors="coerce")
    df = df.dropna()                       # remove rows with any empty value
    df = df[df["Quantity"] > 0]            # remove impossible values
    df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y")
    return df
```

> Order matters: to_numeric first (turns junk into NaN), THEN dropna (removes the NaN).

## 4. Pick columns and filter rows

Filtering is how you answer "show me X". Each condition goes in its own brackets, joined with & (and) or | (or).

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

> Use & and |, never the words and / or. Forgetting the brackets gives "truth value of a Series is ambiguous".

## 5. A numbered menu built FROM the data

Never type the categories or products into your code - read them from the data, so it still works with new data.

```python
def get_valid_number(prompt, minimum, maximum):
    while True:
        choice = input(prompt)
        try:
            choice = int(choice)
        except ValueError:
            print("Please enter a whole number.")
            continue
        if choice < minimum or choice > maximum:
            print(f"Please enter a number from {minimum} to {maximum}.")
        else:
            return choice

def choose_category(df):
    categories = sorted(df["Category"].unique().tolist())
    for number, name in enumerate(categories, start=1):
        print(f"{number}. {name}")
    choice = get_valid_number("Choose a category: ", 1, len(categories))
    return categories[choice - 1]
```

> choice - 1 because lists start at 0 but your menu starts at 1.

## 6. Dates from the user

Trends over time are in every Task 4a. Keep asking until the date is real, then check start is before end.

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

> In May, get_date did return True on a bad date - it must loop and ask again instead.

## 7. Last 7 / 14 / 30 days

The mark scheme names preset timeframes as a higher-level answer. Count back from the newest date in the data.

```python
def last_n_days(df, n):
    latest = df["Date"].max()
    start = latest - pd.Timedelta(days=n - 1)
    return df[df["Date"] >= start].copy()

recent = last_n_days(df, 7)
```

> Use df["Date"].max(), not today - the data may be old.

## 8. Totals, averages, highest and lowest

One line each. Always round money to 2 dp and put words around the number.

```python
total = df["Quantity"].sum()
average = df["Quantity"].mean()
highest = df["Quantity"].max()
lowest = df["Quantity"].min()
rows = len(df)

print(f"Total sold: {total} items in {rows} sales")
print(f"Average per sale: {average:.2f} items")    # 2 decimal places
print(f"Total income: £{1234.5:,.2f}")             # £1,234.50 - commas + 2 dp
```

> :.2f = 2 decimal places. :,.2f also adds commas for thousands.

## 9. New columns: income and profit

Work out a value for every row at once - no loop needed.

```python
def add_income_profit(df):
    df = df.copy()
    df["Income"] = df["Quantity"] * df["Sale Price"]
    df["Profit"] = df["Quantity"] * (df["Sale Price"] - df["Cost Price"])
    return df

df = add_income_profit(df)
print(f"Total profit: £{df['Profit'].sum():.2f}")
```

> Inside an f-string with double quotes, use single quotes for the column name.

## 10. The row with the highest value

Answers questions like "best-selling day" or "most expensive".

```python
best_row = df.loc[df["Income"].idxmax()]          # the whole row
print(f"Best sale: {best_row['Product']} on {best_row['Date']:%d/%m/%Y}")

top5 = df.sort_values("Income", ascending=False).head(5)
```

> idxmax gives the row label of the biggest value; .loc[...] fetches that row.

## 11. Counting things

How many times each value appears.

```python
counts = df["Category"].value_counts()
print(counts)

drinks = counts.get("Drinks", 0)    # 0 if there are none
```

> In May, .get("Gold") printed None when there were no golds. .get("Gold", 0) prints 0.

## 12. Compare groups with groupby

"Compare all categories" is a higher-level answer in the mark scheme. groupby does it in one line.

```python
by_category = df.groupby("Category")["Income"].sum().round(2)
by_category = by_category.sort_values(ascending=False)
print(by_category)

for category, income in by_category.items():
    print(f"{category}: £{income:.2f}")
```

> Read it as: split by Category -> take Income -> add up each group.

## 13. Trends over time

Group by day, week or month to show how something changes.

```python
df["Month"] = df["Date"].dt.strftime("%Y-%m")       # 2026-09, 2026-10 ... sorts correctly
monthly = df.groupby("Month")["Income"].sum().round(2)

daily = df.groupby("Date")["Quantity"].sum()

first, last = monthly.iloc[0], monthly.iloc[-1]
change = (last - first) / first * 100
print(f"Income changed by {change:.1f}% from the first to the last month.")
```

> iloc[0] = first, iloc[-1] = last. Check first is not 0 before dividing.

## 14. Graphs

Line graph for a trend over time, bar chart to compare groups. Always a title and both axis labels.

```python
def show_bar(totals, title, x_label, y_label):
    plt.figure(figsize=(8, 5))
    plt.bar(totals.index, totals.values)
    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def show_line(series, title, x_label, y_label):
    plt.figure(figsize=(8, 5))
    plt.plot(series.index, series.values, marker="o")
    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

show_bar(by_category, "Income by category", "Category", "Income (£)")
```

> In a Codespace plt.show() shows nothing - use plt.savefig("chart.png") to check. In the exam plt.show() works.

## 15. Output that makes sense to the user

Words around every number, no index column, a clear heading.

```python
print("\n--- Drinks sales, 01/10/2026 to 31/10/2026 ---")
print(result[["Date", "Product", "Quantity"]].to_string(index=False))

if result.empty:
    print("No sales found for those dates.")
```

> Check result.empty before calculating - a mean of nothing is NaN, and a graph of nothing is blank.

## 16. The main menu loop

main loads and cleans once, then loops until Exit, passing df into each option.

```python
def main():
    df = load_data("cafe_sales.csv")
    if df is None:
        return
    df = clean_data(df)
    df = add_income_profit(df)

    while True:
        print("\n1. Sales for one category")
        print("2. Compare all categories")
        print("3. Income trend over time")
        print("4. Exit")
        choice = get_valid_number("Choose 1-4: ", 1, 4)
        if choice == 1:
            category_report(df)
        elif choice == 2:
            compare_categories(df)
        elif choice == 3:
            income_trend(df)
        else:
            print("Goodbye.")
            break

main()
```

> In May the menu ran once and had no Exit. This loop fixes both.

## 17. Using the code you are given

Task 4a gives you a Python file. You must USE it, not ignore it.

```python
# Option A - keep their file next to yours and import it
import given_code                      # their file is given_code.py
given_code.some_function(...)

# Option B - copy their function into your file and call it from your menu
```

> Both files must be in the same folder for import to work. Say which option you chose in a comment.

## 18. Comments, names and security

Code organisation (8) and Security (6) are 14 marks - nearly half of Task 4a.

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

> One short comment above each function saying what it is for and what it returns.

## 19. Errors you will probably see

Read the LAST line of the red error first.

```python
KeyError: 'Destination'            -> column name is wrong. print(df.columns)
TypeError: '>' not supported ... 'str' and 'int'
                                   -> forgot pd.to_numeric
TypeError: ... Timestamp and str   -> forgot pd.to_datetime on the column
ValueError: time data ... doesn't match format
                                   -> date text and format= do not match
ValueError: The truth value of a Series is ambiguous
                                   -> used and/or, or forgot the brackets in a filter
SettingWithCopyWarning             -> add .copy() after filtering
NameError: name 'df' is not defined
                                   -> df lives in another function - pass it in
Empty DataFrame                    -> filter matched nothing - check spelling and dates
```

## 20. The whole thing on one page

Every Task 4a solution has this shape. Swap the column names and the menu options.

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
