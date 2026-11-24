# A numbered menu built from the data

*5. A numbered menu built FROM the data*

Never type the options into your code - read them from the data, so it still works when the data changes.

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

> `names[choice - 1]` - lists start at 0, your menu starts at 1.
