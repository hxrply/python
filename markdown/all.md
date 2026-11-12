# Pandas & Matplotlib Quick Cheat Sheet

## Setup

```
import pandas as pd
import matplotlib.pyplot as plt
```

## Load, save, look

```
df = pd.read_csv("data.csv")
df.to_csv("out.csv", index=False)
df.head()            first 5 rows
df.info()            columns + types
df.describe()        quick stats
df.isnull().sum()    missing values
```

## Select

```
df["col"]                one column
df[["a", "b"]]           several columns
df.loc[0, "col"]         by label
df.iloc[0, 0]            by position
```

## Filter

```
df[df["score"] > 70]
df[(df["a"] > 1) & (df["b"] == "x")]     # and
df[(df["a"] > 1) | (df["b"] == "x")]     # or
df[df["col"].isin(["x", "y"])]
df[df["date"].between(start, end)]
```

Use & | ~ with brackets round each condition, never and / or.

## Clean

```
df = df.dropna()
df["col"] = df["col"].fillna(0)
df = df.drop_duplicates()
df["num"] = pd.to_numeric(df["num"], errors="coerce")
df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y")
df["name"] = df["name"].str.strip()
```

Reassign (df = ...) or the change is lost.

## Analyse

```
df["col"].sum()   .mean()   .max()   .count()
df["col"].value_counts()
df.groupby("group")["col"].sum()
df.sort_values("col", ascending=False)
df["total"] = df["price"] * df["qty"]
```

## Plot

```
plt.bar(x, y)          compare categories
plt.plot(x, y)         change over time
plt.pie(y, labels=x)   parts of a whole
plt.hist(y)            spread of values

plt.title("Title")
plt.xlabel("X label")
plt.ylabel("Y label")
plt.legend()
plt.savefig("chart.png")    # before show()
plt.show()

df.groupby("group")["col"].sum().plot(kind="bar")
```

## Common errors

| Error | Fix |
| --- | --- |
| `KeyError` | Column name spelt wrong. Check `df.columns` |
| `truth value is ambiguous` | Use `&` / `\|` with brackets |
| Nothing changed | Reassign: `df = df.dropna()` |
| `SettingWithCopyWarning` | Use `df.loc[...]` or `.copy()` |
| `TypeError` int + str | `pd.to_numeric()` |
| Chart not showing | Add `plt.show()` |
| Saved chart blank | `savefig()` before `show()` |
