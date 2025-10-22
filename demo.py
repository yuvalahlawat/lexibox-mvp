import random
name = input("Greetings! Player, What's your name?")
print(f"Welcome to the quiz,{name}")

def quiz():
    one = "What's 3+2"
    two = "What's 6+5"
    three = "What's 4*3"
    four = "What's 6*8"
    one_sol = [2,5,6,8]
    two_sol = [3,14,11,10]
    three_sol = [12,15,16,18]
    four_sol = [50,42,32,48]
    q_count = 4
    q_list = [one,two,three,four]
    points = 0
    while q_count>0:
        choice = random.choice(q_list)
        q_list.remove(choice)
        print(choice)
        print("Choose your answer from these options")
        q_count-=1

        if choice == one:
            print(one_sol)
            option = int(input("Choose your option from 1-4: "))
            if option == 2:
                print("Hurrah! You got that right (Points +2)")
                points+=2
            else:
                print("Better luck next time! (Points -1)")
                points-=1

        elif choice == two:
            print(two_sol)
            option = int(input("Choose your option from 1-4: "))
            if option == 3:
                print("Hurrah! You got that right (Points +2)")
                points+=2
            else:
                print("Better luck next time! (Points -1)")
                points-=1   

        elif choice == three:
            print(three_sol)
            option = int(input("Choose your option from 1-4: "))
            if option == 1:
                print("Hurrah! You got that right (Points +2)")
                points+=2
            else:
                print("Better luck next time! (Points -1)")
                points-=1  

        elif choice == four:
            print(four_sol)
            option = int(input("Choose your option from 1-4: "))
            if option == 4:
                print("Hurrah! You got that right (Points +2)")
                points+=2
            else:
                print("Better luck next time! (Points -1)")
                points-=1 
    print("Your points are: ",points)
quiz()                  

                 
