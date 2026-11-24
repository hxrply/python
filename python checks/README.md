# python
## Python checker

`python_checker.py` finds problems in a Python file and explains **why** each one is a problem and **how** to fix it.

Set up once:

```
python -m pip install -r requirements.txt
```

Then run:

```
python python_checker.py                                   # asks which file to check
python python_checker.py task_2_summer.py --run            # also runs it to catch crashes
python python_checker.py task_2_summer.py --expected expected.txt   # checks the output too
```

The checker works without the packages, but finds more problems with them installed.
