import pandas as pd

#loads the csv once to be used in other functions not yet used
def load_csv():
    try:
        pd.read_csv("/workspaces/python/Task4a_CretCon_Data.csv.csv")
    except:
        FileNotFoundError
        print("File Not Found")
    return None





#Outputs the main menu and checks the user input
def main_menu():
    valid = False

    while valid == False:

        print("-"*54)
        print("------------- Management Data Dashboard ------------- ")
        print("-"*54)
        print("")
        print("--------------------- Main Menu --------------------- ")
        print("1. Attendance Analysis")
        print("2. Popularity Of Event Types")
        print("3. Money Generated From Different Sources")
        print("-"*54)

        try:
            choice = int(input('Enter your number selection here: '))
        except:
            ValueError
            print("Enter a Menu Number Choice")
            return False

        
        if choice == 1:
            return choice
        elif choice == 2:
            return choice
        elif choice == 3:
            return choice
        else:
            print("Sorry, You did not enter a valid option")
            return False
        
    return int(choice)








def get_event(event_type):
    
    flag = True
    
    while flag:
        event = input('Please enter Event Type: '.format(event_type))

        try:
           pd.to_datetime(event)
        except:
            print("Sorry, you did not enter a valid Event")
            flag = True
        else:
            flag = False
    
    return event




def get_event_type(start_date, end_date):

    all = pd.read_csv("/workspaces/python/Task4a_CretCon_Data.csv.csv")
    
    all["Event Type"] = pd.to_datetime(all["Event Type"], errors="raise")
    
    event_range = (all["Event Type"] >= pd.to_datetime(start_date, format="%d/%m/%Y")) & \
                 (all["Event Type"] <= pd.to_datetime(end_date,format="%d/%m/%Y" ))
        
    event_extract = all.loc[event_range]
        
    return event_extract




def calculate_total_attendance(event_extract, start_date, end_date):

        all = event_total_extract = event_extract.groupby(['Event Type'], as_index=False) ['Attendance'].sum()
        extract_no_index = event_total_extract.to_string(index=False)
    
        print("Here is the total attendance between {} and {} for the Event:".format(start_date, end_date))
        print(extract_no_index)












#gets a date from the user and check date is in correct format.
def get_date(start_end):
    
    flag = True
    
    while flag:
        date = input('Please enter {} date for your date range (DD/MM/YYYY) : '.format(start_end))

        try:
           pd.to_datetime(date, format="%d/%m/%Y")
        except:
            print("Sorry, you did not enter a valid date")
            flag = True
        else:
            flag = False
    
    return date







def get_data_by_date_range(start_date, end_date):

    all = pd.read_csv("/workspaces/python/Task4a_CretCon_Data.csv.csv")

    all["Date"]= pd.to_datetime(all["Date"], format="%d/%m/%Y", errors="raise")

    date_range = (all["Date"] >= pd.to_datetime(start_date, format="%d/%m/%Y")) & \
                  (all["Date"] <= pd.to_datetime(end_date,format="%d/%m/%Y" ))
    
    date_extract = all.loc[date_range]
    
    return date_extract






def calculate_average_attendance(date_extract, start_date, end_date):

        all = venue_mean_extract = date_extract.groupby(['Venue'], as_index=False) ['Attendance'].mean()
        extract_no_index = venue_mean_extract.to_string(index=False)
    
        print("Here is the average attendance between {} and {} for each venue:".format(start_date, end_date))
        print(extract_no_index)








main_menu_choice = main_menu()

if main_menu_choice == 1:
    load_csv()
    start_date = get_date("start")
    end_date = get_date("end")
    date_extract = get_data_by_date_range(start_date, end_date)
    calculate_average_attendance(date_extract, start_date, end_date)


if main_menu_choice == 2:
    load_csv()
    start_date = get_date("start")
    end_date = get_date("end")
    event_type = get_event("event_type")
    event_extract = get_event_type(start_date, end_date)
    calculate_total_attendance(event_extract, start_date, end_date)
    
   


if main_menu_choice == 3:
    load_csv()
    print("hey")