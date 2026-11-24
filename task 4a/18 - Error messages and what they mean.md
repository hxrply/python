# Read the LAST line of the error first

*Errors you will probably see*

Find the last line of the red error in the left column, do what the right column says.

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
