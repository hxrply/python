# Load the CSV once

*Import and load the CSV once*

Like loading a save file. Do it once in main, then pass **df** to everything else. `try` = attempt the jump, `except` = the checkpoint if you fall.

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

> In `except`, df was never made - return **None**, not df.
