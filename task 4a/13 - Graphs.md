# Graphs - your biggest gap from May

*Graphs*

**Line** for a trend over time. **Bar** to compare groups. Always a **title**. Always **both axis labels**.

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

> Codespace: `plt.show()` shows nothing - use `plt.savefig("chart.png")`. In the exam `plt.show()` works.
