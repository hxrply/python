from datetime import datetime

venue_types = ("Arena", "Conference Hall", "Small Exhibition Hall")

#gets and validates customer name
def get_name():
    
    valid = False

    while valid == False: 
        name = input("Please enter customer name: ")

        if name.replace(" ","").isalpha():
            print ("Name Accepted!")
            return name
        else:
            print("Sorry you have not entered a valid name")

#gets the booking date, checks format and if in the future
def get_date():
    current = datetime.now()

    valid = False
    while valid == False:
        date_string = input('Please enter the date of the booking (DD/MM/YYYY): ')

        date_format = '%d/%m/%Y'

        try:
            date = datetime.strptime(date_string, date_format)
        except ValueError:
            print("Invalid date format. Please use DD/MM/YYYY.")
            continue

        if date > current:
            print ("Date Accepted!")
            return date_string
        else:
            print("Date for booking must be in the future.")

#gets and validates the length of the booking
def get_num_hours():
    valid = False
    while valid == False:
        number_hours = input('Please enter the length of the booking (hours): ')

        if number_hours.isdigit():
            if int(number_hours) <=72 and int(number_hours) >=6:
                print ("Number Accepted!")
                return int(number_hours)
            else:
                print("number must be between 6 and 72")
        else:
            print("Input must be a number")

#gets and validates the number of people expected to attend
def get_number_people():
    
    valid = False
    while valid == False:
        number_people = input('Please enter the number of people expected to attend: ')

        if number_people.isdigit():
            if int(number_people) > 0:
                print ("Number Accepted!")
                return int(number_people)
        else:
            print("Input must be a number")

#determines which type of venue is needed based on the number of people
def get_venue(number_people):
    
    if number_people <= 1000:
        venue = venue_types[2]
    elif number_people <= 5000:
        venue = venue_types[1]
    elif number_people <= 15000:
        venue = venue_types[0]
    else:
        print("Sorry, we do not have a venue big enough for this many people")
        exit()

    return venue  

#calculates the booking fee
def  get_booking_fee(venue, num_hours):
    if venue == "Small Exhibition Hall":
        booking_fee = num_hours * 175
    elif venue == "Conference Hall":
        booking_fee = num_hours * 380
    else:
        booking_fee = num_hours * 995

    return float(booking_fee)

#calculates the length of booking surcharge
def calc_length_surcharge(num_hours, booking_fee):
    if num_hours <= 8:
        length_charge = booking_fee * 0.15
    else:
        length_charge = 0

    return length_charge

#calculates the merchandise surcharge
def calc_merch_surcharge(booking_fee):
    valid = False

    while valid == False:
        merch_sale = input("Will you be selling merchandise: (Y/N)")

        if merch_sale == "Y" or merch_sale == 'y':
            merch_surcharge = booking_fee * 0.075
            valid = True
        elif merch_sale == "N" or merch_sale == 'n':
            merch_surcharge = 0
            valid = True
        else:
            print("Sorry you have not entered a valid option. Please try again")

    return merch_surcharge


def main():
    name = get_name()
    date = get_date()
    hours = get_num_hours()
    number_people = get_number_people()
    venue = get_venue(number_people)
    booking_fee = get_booking_fee(venue, hours)

    length_surcharge = calc_length_surcharge(hours, booking_fee)

    security_staff_required = number_people / 30 
    first_aid_staff_required = number_people / 50
    food_staff_required = number_people / 200

    security_staff_cost = security_staff_required * (hours * 23)

    first_aid_staff_cost = first_aid_staff_required * (hours * 32)

    food_staff_cost = food_staff_required * (hours * 17.50)

    merchandise_surcharge = calc_merch_surcharge(booking_fee)

    staff_cost = security_staff_cost + first_aid_staff_cost + food_staff_cost

    subtotal = booking_fee + staff_cost 

    total_cost = subtotal + length_surcharge + merchandise_surcharge

    print("-"*60)
    print("Booking Quotation Summary")
    print("-"*60)
    print("Name of customer: ", name)
    print("Date of booking: ", date)   
    print("Number of people to attend: ", number_people)
    print("Length of booking: {} hours".format(hours))
    print("-"*60)
    print("For {} people, we recommend the {} venue".format(number_people, venue))
    print("The base booking fee for the {} venue is £{}".format(venue, booking_fee))
    print("You will require {} members of security staff at a cost of £{}".format(security_staff_required, security_staff_cost))
    print("You will require {} members of first aid staff at a cost of £{}".format(first_aid_staff_required, first_aid_staff_cost))
    print("You will require {} members of food outlet staff at a cost of £{}".format(food_staff_required, food_staff_cost))
    print("Cost of staff: £{}".format(staff_cost))
    print("-"*60)
    print("Subtotal (booking fee + Staff costs): £{} ".format(subtotal))
    print("Length surcharge: £{} ".format(length_surcharge))
    print("Merchandise surcharge: £{}".format(merchandise_surcharge))
    print("Final total (inc all charges): £{}".format(total_cost))

main()
