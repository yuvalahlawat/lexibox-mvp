import random


def load_questions():
    return [
    { "question": "What's 3+2", "soln": [2, 5, 6, 8], "Correct_index": 1 },
    { "question": "What's 6+5", "soln": [3, 14, 11, 10], "Correct_index": 2 },
    { "question": "What's 4*3", "soln": [12, 15, 16, 18], "Correct_index": 0 },
    { "question": "What's 6*8", "soln": [50, 42, 32, 48], "Correct_index": 3 },
    { "question": "What's 3*8", "soln": [50, 24, 32, 48], "Correct_index": 1 }
]

def ask_question(q):
    options = q["soln"][:]  # Copy the options list
    correct = q["soln"][q["Correct_index"]]
    random.shuffle(options)

    print("\n" + q["question"])
    
    for i, opt in enumerate(options):
        print(f"{i+1}. {opt}")  # This loop prints ALL options

    try:
        choice = int(input("Enter your choice (1-4): "))
        if 1 <= choice <= 4:
            return options[choice - 1] == correct
        else:
            print("❌ Invalid choice.")
            return False
    except:
        print("❌ Invalid input.")
        return False

def quiz():
    name = input("What's your name? ")
    questions = load_questions()
    random.shuffle(questions)
    score = 0
    for q in questions:
        result = ask_question(q)
        if result:
            score+=2
            print(f"Your answer is correct.\nScore: {score}")
        else:
            score-=1
            print(f"Your answer is incorrect.\nScore: {score}")   

    print (f"Final score: {score}")         
    with open("Score_file.txt","a") as f:
        f.write(f"\n{name} scored {score} points.")


def return_score():
    with open("Score_file.txt","r") as f:
        print("\nScore History: \n")
        print(f.read())

    


while True:
    
    print("\n[1] Play Quiz\n[2] View Score History\n[3] Exit")
    try :
        play_choice = int(input("What do you want to do?(Choose 1-3): "))
        if play_choice == 1:
            quiz()
            
            
        elif play_choice==2:
            return_score()
        else: 
            print("Goodbye! ")
            break
    except:
        print("Invalid Input")
        continue        

  

 
            

