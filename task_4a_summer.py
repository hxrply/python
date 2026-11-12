import pandas as pd
import matplotlib.pyplot as plt



# function to read csv and verify if it can be used for analysis and if not states 
# the error and asks again (might be used)
def read_csv():
    all_data = pd.read_csv("Task4a_Glenstar_data.csv")
    while True:
        try:
            read_csv(all_data)
            print("Valid CSV entry")
            return None
        
        except Exception as e:
            print(e)
            print("Try again")



# updated the function to get rid of the unnessicery valid = true and false checks
# Outputs the main menu and checks the user input
def main_menu():

    total_options = 3

    while True:

        print("-"*70)
        print("---------- Athlete Performance Analysis Module ------------- ")
        print("-"*70)
        print("")
        print("--------------------- Main Menu --------------------- ")
        print("1. Places achieved by athlete")
        print("2. Performance of athlete in different rule sets")
        print("3. Prize money won by athlete")
        
        choice = input('Enter your number selection here: ')

        try:
            choice = int(choice)
            if choice < 1 or choice > total_options:
               print("Sorry, you did not enter a valid option") 
            else:    
                print('Choice accepted!')
                return choice
        except:
            print("Sorry, you did not enter a valid option")



# collects the users desired athlete of choice
def get_athlete_names ():

    df = pd.read_csv("Task4a_Glenstar_data.csv")

    athletes = df["Athlete"].unique().tolist()

    valid = False

    while valid == False:

        print("-"*70)
        print("---------- Athlete Performance Analysis Module ------------- ")
        print("-"*70)
        print("")
        print("--------------------- Athlete Positions Menu --------------------- ")
        print("Select an athlete:")
        for i in range(len(athletes)):
            print(i+1, " ", athletes[i])

        choice = input('Enter your number selection here: ')

        try:
            choice = int(choice)
            if choice < 1 or choice > len(athletes):
               print("Sorry, you did not enter a valid option") 
            else:    
                print('Choice accepted!')
                chosen_athlete = athletes[choice -1]
                return chosen_athlete
        except:
            print("Sorry, you did not enter a valid option")
   
    print("You have selected athlete: ",chosen_athlete)



#creating a function which will identify the rule sets for the selected athlete
def get_rule_sets():

    df = pd.read_csv("Task4a_Glenstar_data.csv")
    rule_sets = df["Rule Set"].unique().tolist()

    while True:

        print("-"*70)
        print("---------- Rule Set Module ------------- ")
        print("-"*70)
        print("")
        print("--------------------- Rule Set Menu --------------------- ")
        print("Select a Rule Set:")
        for i in range(len(rule_sets)):
            print(i+1, " ", rule_sets[i])

        choice = input('Enter your number selection here: ')

        try:
            choice = int(choice)
            if choice < 1 or choice > len(rule_sets):
               print("Sorry, you did not enter a valid option") 
            else:    
                print('Choice accepted!')
                chosen_rule_set = rule_sets[choice -1]
                print("You have selected rule_set: ",chosen_rule_set)
                return chosen_rule_set
        except:
            print("Sorry, you did not enter a valid option")



def get_date(start_end): # updated this part of code to be more clean without using flags
    
    while True:
        date = input('Please enter {} date for your date range (DD/MM/YYYY) : '.format(start_end))

        try:
           pd.to_datetime(date, format="%d/%m/%Y")
        except:
            print("Sorry, you did not enter a valid date")
            return True
        else:
            return date



# function to take in all the information to prepare for the final function and gathers all the filtered data
# filters between judo and jiu jitsu information and allows for proper analysis of certain rule sets
def get_information_by_rule_sets_and_date(athlete, rule_sets, start_date, end_date):
    
    df = pd.read_csv("Task4a_Glenstar_data.csv")
    rule_set_data = df.loc[df["Rule Set"] == rule_sets] # trying to filter rule set data to be specific to both the athlete and rule set
    rule_set_data_filtered  =  rule_set_data.loc[df["Athlete"] == athlete] # need to figure out how to filter in both categories because with this code it is not filtering the rule sets (done now and filters between judo and jiu jitsu)

    rule_set_data_filtered["Date"] = pd.to_datetime(rule_set_data["Date"], format = "%d/%m/%Y", errors = "raise")

    date_range = (rule_set_data_filtered["Date"] >= pd.to_datetime(start_date, format = "%d/%m/%Y")) & \
                    (rule_set_data_filtered["Date"] <= pd.to_datetime(end_date, format = "%d/%m/%Y" ))
    
    rule_set_extract = rule_set_data_filtered.loc[date_range]

    return rule_set_extract



def get_data_by_athlete_and_date(athlete, start_date, end_date):
    
    all = pd.read_csv("Task4a_Glenstar_data.csv")
    athlete_data = all.loc[all["Athlete"] == athlete].copy()

    athlete_data["Date"]= pd.to_datetime(athlete_data["Date"], format = "%d/%m/%Y", errors = "raise")
    
    date_range = (athlete_data["Date"] >= pd.to_datetime(start_date, format="%d/%m/%Y")) & \
                  (athlete_data["Date"] <= pd.to_datetime(end_date,format="%d/%m/%Y" ))
    
    athlete_extract = athlete_data.loc[date_range]

    return athlete_extract



#calculates the rule set placements
def calculate_places_rule_set (rule_set_extract, athlete, rule_set, start_date, end_date):
    
    gold = rule_set_extract['Place'].value_counts().get("Gold")
    silver = rule_set_extract['Place'].value_counts().get("Silver")
    bronze = rule_set_extract['Place'].value_counts().get("Bronze")
    top = rule_set_extract['Place'].value_counts().get("Top 10")
    no_place = rule_set_extract['Place'].value_counts().get("Not Placed")



    print("Here is the break down of the performance of {} in {} between {} and {}: ".format(athlete, rule_set, start_date, end_date))
    print("Gold medals: ", gold)
    print("Silver medals:", silver)
    print("Bronze medals: ", bronze)
    print("Top 10: ", top)
    print("Not placed: ", no_place)



# calculates the athlete placements specific to the athlete
def calculate_places_athlete (athlete_extract, athlete, start_date, end_date):
    
    gold = athlete_extract['Place'].value_counts().get("Gold")
    silver = athlete_extract['Place'].value_counts().get("Silver")
    bronze = athlete_extract['Place'].value_counts().get("Bronze")
    top = athlete_extract['Place'].value_counts().get("Top 10")
    no_place = athlete_extract['Place'].value_counts().get("Not Placed")



    print("Here is the break down of the performance of {} between {} and {}: ".format(athlete, start_date, end_date))
    print("Gold medals: ", gold)
    print("Silver medals:", silver)
    print("Bronze medals: ", bronze)
    print("Top 10: ", top)
    print("Not placed: ", no_place)



def calculate_prize_money(athlete_extract, athlete, start_date, end_date):

    Money = athlete_extract['Prize Money'].sum()

    print("Here is the Total of the Prize Money of {} between {} and {} is £{}: ".format(athlete, start_date, end_date, Money))



# a line graph which shows athlete performance in a date range (would like to do this for every main menu choice option)
#def placement_athlete_line_chart(calculate_places_athlete, athlete_extract, athlete, start_date, end_date):

#plt.bar(gold color = "blue", label="blue")

#plt.title("Example bar")
#plt.xlabel(athlete)
#plt.ylabel("Medals")
#plt.show()
#plt.savefig("medal_info.png")



main_menu_choice = main_menu()



# the first menu choice which takes in an athlete name and date range and returns the placements they recieved
if main_menu_choice == 1:
    athlete = get_athlete_names()
    start_date = get_date("start")
    end_date = get_date("end")
    athlete_extract = get_data_by_athlete_and_date(athlete, start_date, end_date)
    calculate_places_athlete (athlete_extract, athlete, start_date, end_date)
    # placement_athlete_line_chart (calculate_places_athlete, athlete_extract, athlete, start_date, end_date)
    # would have wanted to add matplotlib fnctions but dont know how to do that



# creating a second menu choice which will take in the athletes name and then prompt for the user to enter a specific 
# rule set which will then be filtered by date to show how that athlete performs in the certain rule set.
if main_menu_choice == 2:
    athlete = get_athlete_names() # gets athlete for analysis
    rule_sets = get_rule_sets() # asking the user for a choice of rule set 
    start_date = get_date("start") # selecting start date
    end_date = get_date("end") # selecting end date
    rule_set_extract = get_information_by_rule_sets_and_date(athlete, rule_sets, start_date, end_date)
    calculate_places_rule_set (rule_set_extract, athlete, rule_sets, start_date, end_date)



# menu choice 3 takes in an athletes name and date range and calculates the amount of money won in that time range
if main_menu_choice == 3:
    athlete = get_athlete_names() # gets athlete for analysis
    start_date = get_date("start")
    end_date = get_date("end")
    athlete_extract = get_data_by_athlete_and_date(athlete, start_date, end_date)
    calculate_prize_money (athlete_extract, athlete, start_date, end_date)