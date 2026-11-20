I found 9 problems. The biggest is a calculation error that makes every short booking cost about twice what it should. I’ve listed them from most to least serious.

1. Length surcharge is 115%, not 15% (logic error)
python
length_charge = booking_fee * 1.15

This charges the whole booking fee again plus 15% on top. A 15% surcharge should be:

python
length_charge = booking_fee * 0.15
2. Lowercase “n” isn’t accepted for merchandise
python
elif merch_sale == "N" or merch_sale == 'N':

Both checks are for capital "N", so typing n says the option isn’t valid. It should be merch_sale == "N" or merch_sale == "n". A neater version is merch_sale.upper() == "N", and the same works for the Y check.

3. A badly typed date crashes the program

If the user types something like 25-12-2026 or hello, datetime.strptime raises a ValueError and the program stops. Wrap it in a try/except:

python
try:
    date = datetime.strptime(date_string, date_format)
except ValueError:
    print("Invalid date format. Please use DD/MM/YYYY.")
    continue
4. Numbers outside the allowed range give no error message

In get_num_hours, entering 3 or 100 passes isdigit() but fails the range check. Nothing is printed, so the question just repeats with no explanation. get_number_people does the same when you enter 0. Add an inner else:

python
if number_hours.isdigit():
    if 6 <= int(number_hours) <= 72:
        print("Number Accepted!")
        return int(number_hours)
    else:
        print("Booking must be between 6 and 72 hours")
else:
    print("Input must be a number")
5. Staff numbers can be fractions

number_people / 30 gives answers like 33.333 security staff, and you can’t hire a third of a person. Round up with math.ceil:

python
import math
security_staff_required = math.ceil(number_people / 30)
first_aid_staff_required = math.ceil(number_people / 50)
food_staff_required = math.ceil(number_people / 200)

Check your brief for the exact rule, but rounding up is the usual one.

6. Money isn’t formatted to 2 decimal places

Prices print as £1234.5 or £766.6666666667. Use {:.2f} in every money print:

python
print("Final total (inc all charges): £{:.2f}".format(total_cost))
7. Names with spaces are rejected

"Jack Harpley".isalpha() is False because of the space, so a full name never gets through. If full names should be allowed:

python
if name.replace(" ", "").isalpha():

That would also accept a name made only of spaces, so add a check like name.strip() != "" if that matters for your brief.

8. Small things
Typo: the comment on line 5 says “customet” instead of “customer”.
exit(): exit() in get_venue is meant for the interactive shell. sys.exit() (after import sys) is the proper way to stop a script.
Unused variable: valid is never changed in most of the loops, so while True: would be clearer.