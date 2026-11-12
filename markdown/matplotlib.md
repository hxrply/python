# Matplotlib Cheat Sheet – T Level DSD ESP

## Setup

```
import matplotlib.pyplot as plt
```

## Every chart needs

- A title
- Both axis labels, with units (e.g. £ for money)
- A legend if there are 2 or more lines

## Basic chart

```
plt.plot(x, y, label="2026")
plt.title("Sales by month")
plt.xlabel("Month")
plt.ylabel("Sales (£)")
plt.legend()
plt.savefig("chart.png")       # BEFORE show()
plt.show()
```

## Chart types

| Code | Chart | Use it for |
| --- | --- | --- |
| `plt.plot(x, y)` | Line | Change over time |
| `plt.bar(names, values)` | Bar | Comparing categories |
| `plt.barh(names, values)` | Sideways bar | Long names |
| `plt.scatter(x, y)` | Scatter | Link between 2 numbers |
| `plt.hist(values, bins=10)` | Histogram | Spread of one number |
| `plt.pie(values, labels=names, autopct="%1.1f%%")` | Pie | Parts of a whole |

## Styling

```
plt.plot(x, y, color="red", linestyle="--", marker="o")
plt.grid(True)
plt.xticks(rotation=45)        # stop labels overlapping
plt.tight_layout()             # stop labels being cut off
```

## Subplots (2 or more charts in one window)

```
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
axes[0].bar(names, scores)
axes[0].set_title("Scores")    # ax uses set_title, set_xlabel
axes[1].hist(scores)
axes[1].set_xlabel("Score")
plt.tight_layout()
plt.show()
```

## Plot from pandas

```
df.plot(x="month", y="sales", kind="line")
df.groupby("Athlete")["Prize Money"].sum().plot(kind="bar")
df["Prize Money"].plot(kind="hist")
plt.show()
```

## Common defects

| Problem | Fix |
| --- | --- |
| Chart never appears | Missing `plt.show()` |
| Saved image is blank | `savefig()` must come before `show()` |
| Legend empty | Add `label="..."` to each plot, then `plt.legend()` |
| `x and y must have same first dimension` | Lists are different lengths |
| `'Axes' object has no attribute 'title'` | With `ax` use `ax.set_title()`, `ax.set_xlabel()` |
| Labels overlap or are cut off | `plt.xticks(rotation=45)`, `plt.tight_layout()` |
| Weird axis, numbers treated as text | `pd.to_numeric()` the column first |
