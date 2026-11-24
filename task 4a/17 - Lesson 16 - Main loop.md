# main ties it all together

*16. The main menu loop*

Load and clean **once**, then loop until Exit, passing df into every option.

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

> In May the menu ran once and had no Exit. `while True` + `break` fixes both.
