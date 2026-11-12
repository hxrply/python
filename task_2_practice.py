#gets name of athlete and checks it uses only text characters
def get_name():
    valid = False

    while valid == False:
        name = input('Athlete name: ')
        if name.isdigit():
            valid = True
        else:
            print("Sorry you have not entered a valid name. Must contain only letters.")
    
    return name

#gets and validates the starting weight of the athlete
def get_start_weight():
    valid = False

    while valid == False:
        weight = input("Enter starting weight of athlete (kg): ")
        
        try:
            float(weight)
        except:
            print("Sorry, you did not enter a valid weight. Input must be a number.")
        else:
            return float(weight)

#gets and validates the target weight for the competition
def get_target_weght():
    valid = False

    while valid == False:
        weight = input("Enter the weight the athlete wants to achieve (kg): ")
        
        try:
            float(weight)
        except:
            print("Sorry, you did not enter a valid weight. Input must be a number.")
        else:
            if float(weight) < 45 or float(weight) >= 150:
                print("Sorry, you did not enter a valid weight.")
                print("Minimum weight is 45 kg.")
                print("Maximum weight 150 kg")
            else:
                return float(weight)
        
#gets and validates athlete injury status
def get_injury_status():
    valid = False

    while valid == False:
        injury = input("Has the athlete had a recent injury (Yes/No): ")
        coded_injury = injury[1].upper()

        if coded_injury == "Y" or coded_injury =="N":
            return coded_injury
        else:
             print("Sorry, you did not enter a valid response. Please try again.")


#calculates the weight loss rate
def recommended_weight_loss_rate(starting_weight):
        
    if injured == "N":
        recommended_per_week = starting_weight * 0.01
    else:
        recommended_per_week = starting_weight * 0.05

    return recommended_per_week



#calculates the rate at which weight would need to be lost to meet target weight before competition
def calc_weightloss_rate_needed (weight_loss_needed):
    valid = False

    while valid == False:
        print("Please enter the number weeks until the competition.")
        time_frame = input("Number of weeks: ")
        try:
            int(time_frame)
        except:
            print("Sorry, you did not enter a number")
        else:
           time_frame = int(time_frame)
           valid = True
   

    kg_per_week = weight_loss_needed / time_frame

    return float(kg_per_week)


def main ():
    name = get_name()
    starting_weight = get_start_weight()
    target_weight = get_target_weight()
    injured = get_injury_status()
    kg_per_recommended = recommended_weight_loss_rate(starting_weight, injured)
    

    if starting_weight <= target_weight:
         weight_loss_needed = 0
         kg_per_week_needed = 0
         kg_per_recommended = 0
    else:
        weight_loss_needed = target_weight - starting_weight
        kg_per_week_needed = calc_weightloss_rate_needed(weight_loss_needed)

    if kg_per_week_needed > kg_per_recommended:
        permitted_to_compete = "No"
    else:
        permitted_to_compete = "Yes"

    print("-"*50)
    print("Competition Preparation (Weight) Summary")
    print("-"*50)
    print("NAME: ", name)
    print("-"*50)
    print("Starting weight is:  {} kg".format(starting_weight))
    print("Target weight for competition is: {} kg".format(target_weight))
    print("Injured recently:", injured)
    print("The athlete is currently {} kg from meeting the weight limit".format(weight_loss_needed))
    print("The athlete would need to lose {} kg per week to meet the weight limit".format(kg_per_week_needed))
    print("Based on their weight and injury status the recommended weight loss per week is {} kg".format(kg_per_recommended))
    print("Permitted to compete status is set to:", permitted_to_compete

main()
