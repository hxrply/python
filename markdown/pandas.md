# Pandas Cheat Sheet – T Level DSD ESP

Includes filtering for Task 4a (Glenstar data).

## Setup

```
import pandas as pd
import numpy as np
```

## Golden rule

Most methods return a **new copy**. Reassign it or the change is lost.

```
df = df.dropna()        # correct
df.dropna()             # wrong - change is lost
```

## The Glenstar data

- Columns: `Date`, `Athlete`, `Rule Set`, `Place`, `Prize Money`
- Places: Gold, Silver, Bronze, Top 10, Not Placed
- Rule sets: Judo, Jiu-Jitsu
- Dates: DD/MM/YYYY (Jan to Apr 2026)
- `Rule Set` and `Prize Money` have spaces, so always use `df["Rule Set"]`

## Load once (not in every function)

```
PLACE_ORDER = ["Gold", "Silver", "Bronze", "Top 10", "Not Placed"]
MEDALS = ["Gold", "Silver", "Bronze"]

def load_data(filename):
    try:
        df = pd.read_csv(filename, encoding="utf-8")
    except FileNotFoundError:
        print("Error: data file not found.")
        return None
    df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y")
    df["Month"] = df["Date"].dt.to_period("M")
    return df
```

## Save

```
df.to_csv("out.csv", index=False)    # index=False = no "Unnamed: 0" column
```

## Inspect (do this straight after loading)

```
df.head()                  first 5 rows
df.shape                   (rows, cols) - no brackets
df.columns                 column names
df.info()                  types + non-null counts
df.describe()              stats for number columns
df.isnull().sum()          missing values per column
df["col"].unique()         list of different values
df["col"].value_counts()   count of each value
```

## Select

```
df["name"]                 one column
df[["name", "score"]]      several columns (double brackets)
df.loc[0, "name"]          by LABEL    (slice includes end)
df.iloc[0, 0]              by POSITION (slice excludes end)
```

## Secure date input (loops until valid)

```
def get_date(prompt):
    while True:
        text = input(prompt).strip()
        try:
            return pd.to_datetime(text, format="%d/%m/%Y")
        except ValueError:
            print("Invalid date, use DD/MM/YYYY")

# then check the range makes sense
if start > end:
    print("Start date must be before end date")
```

## Filter: one condition

```
df[df["Athlete"] == "Aisha Khan"]
df[df["Rule Set"] == "Judo"]
df[df["Place"] == "Gold"]
df[df["Prize Money"] > 0]
df[df["Place"].isin(MEDALS)]          # any medal
df[~df["Place"].isin(MEDALS)]         # no medal
```

## Filter: date range

```
df[(df["Date"] >= start) & (df["Date"] <= end)]
df[df["Date"].between(start, end)]    # same thing, inclusive
```

## Filter: combine in one mask

```
mask = ((df["Athlete"] == athlete) &
        (df["Rule Set"] == rule_set) &
        (df["Date"] >= start) &
        (df["Date"] <= end))
extract = df.loc[mask].copy()         # .copy() stops SettingWithCopyWarning
```

Use `&` for and, `|` for or, `~` for not. Put brackets round **every** condition. Never use `and` / `or` / `not`.

## Change matching rows

```
df.loc[df["score"] < 40, "grade"] = "Fail"
```

## Check for no results

```
if extract.empty:
    print("No results for that athlete in that date range")
```

## Count places (shows 0, not None)

```
counts = extract["Place"].value_counts().reindex(PLACE_ORDER, fill_value=0)
for place, n in counts.items():
    print(f"{place:<12}{n}")

(extract["Place"] == "Gold").sum()    # count one thing
extract["Prize Money"].sum()
```

## Sort

```
df.sort_values("score", ascending=False)
df = df.reset_index(drop=True)        # renumber after filter/sort
```

## Clean

```
df = df.dropna(subset=["score"])
df["score"] = df["score"].fillna(0)
df = df.drop_duplicates()
df["price"] = pd.to_numeric(df["price"], errors="coerce")   # text -> number
df["age"] = df["age"].astype(int)                           # fill NaN first
df["name"] = df["name"].str.strip().str.title()
df.columns = df.columns.str.strip()
df = df.rename(columns={"Nm": "name"})
df = df.drop(columns=["notes"])
```

## New columns

```
df["total"] = df["price"] * df["qty"]
df["result"] = np.where(df["score"] >= 50, "Pass", "Fail")
df["grade"] = df["score"].apply(my_function)
```

## Stats

```
.sum()  .mean()  .median()  .min()  .max()  .count()  .round(2)
```

## Group by

```
df.groupby("Athlete")["Prize Money"].sum()
df.groupby("Rule Set")["Prize Money"].agg(["sum", "mean", "count"])
df.groupby("Athlete")["Prize Money"].sum().reset_index()
```

## Merge / join

```
pd.merge(orders, customers, on="customer_id", how="left")
pd.concat([df1, df2], ignore_index=True)
```

## Common defects

| Error or problem | Fix |
| --- | --- |
| `KeyError: 'Score'` | Wrong column name, case or spaces. Check `df.columns` |
| `truth value of a Series is ambiguous` | Used `and` / `or`. Use `&` / `\|` with brackets |
| Data didn't change | Not reassigned. `df = df.dropna()` |
| `SettingWithCopyWarning` | Use `df.loc[condition, "col"] = value`, or `.copy()` after filtering |
| `TypeError` int + str | Numbers stored as text. `pd.to_numeric()` |
| `cannot convert float NaN to integer` | `fillna()` before `astype(int)` |
| Extra `Unnamed: 0` column | `to_csv(..., index=False)` |
| `no attribute 'sort'` | It's `sort_values()` |
| `IndexError` out-of-bounds | `iloc` past the last row. Check `len(df)` |
| Wrong dates | `pd.to_datetime(..., format="%d/%m/%Y")` |

## Fixes for your own code

| In your code | Fix |
| --- | --- |
| `get_date()` does `return True` on a bad date | Loop again instead (see secure date input) |
| `value_counts().get("Gold")` prints `None` when 0 | `.reindex(PLACE_ORDER, fill_value=0)` |
| `rule_set_data.loc[df["Athlete"] == athlete]` | Mask from `df` used on a subset. Build one combined mask |
| `rule_set_data_filtered["Date"] = ...` warning | Filtered without `.copy()`. Add `.copy()` |
| `pd.read_csv` in every function | Load once in `load_data()`, pass `df` in |
| `read_csv()` calls itself | Delete it, use `load_data()` with try/except |
| Bare `except:` | `except ValueError:` (catch the real error) |
| No check that start is before end, no empty check | Add both (see above) |
| Variable called `all` | Shadows Python's `all()`. Rename, e.g. `all_data` |
| Menu runs once then ends | `while True` loop plus a "4. Exit" option |

## Test your fix

```
assert df["Prize Money"].isnull().sum() == 0
print(df.head())
df.info()
```
