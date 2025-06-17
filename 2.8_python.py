TEAM_BUDGET = 1500000
TEAM_SIZE = 6
MAX_MEN = 4
MAX_WOMEN = 2

import sqlite3
conn = sqlite3.connect('fantasy.DB')
cursor = conn.cursor()

def login_user(cursor):
    username = input("Enter username: ")
    password = input("Enter password: ")

    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()

    if user:
        print("Login successful!")
        if user[3] == 1:
            print("Logged in as admin.")
        else:
            print("Logged in as regular user.")
        return user
    else:
        print("Invalid username or password.")
        return None

def create_account(cursor, conn):
    print("\n--- Create Account ---")
    while True:
        username = input("Enter a new username: ").strip()
        if len(username) < 4:
            print("Username must be at least 4 characters long.")
            continue
        if " " in username:
            print("Username cannot contain spaces.")
            continue
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            print("Username already taken. Please choose another.")
        else:
            break

    while True:
        password = input("Enter a password: ").strip()
        if len(password) < 6:
            print("Password must be at least 6 characters long.")
        elif " " in password:
            print("Password cannot contain spaces.")
        else:
            break

    cursor.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, 0)", (username, password))
    conn.commit()

    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    new_user = cursor.fetchone()

    print("Account created successfully! You are now logged in.\n")
    return new_user


def login_or_register(cursor, conn):
    while True:
        choice = input("Do you want to \n(1) Login \n(2) Create a new account? \nEnter 1 or 2: ")

        if choice == '1':
            user = login_user(cursor)
            if user:
                return user
            else:
                print("Login failed, please try again.")
        elif choice == '2':
            user = create_account(cursor, conn)
            return user
        else:
            print("Invalid input. Please enter 1 or 2.")


def display_available_riders(cursor):
    cursor.execute("SELECT name, cost FROM riders")
    riders = cursor.fetchall()

    print("No.  | Name                 | Cost")
    print("-------------------------------------")
    for i, (name, cost) in enumerate(riders, start=1):
        print(f"{str(i).ljust(4)} | {name.ljust(25)} | ${cost}")

def fetch_rider_by_id(cursor, rider_id):
    cursor.execute("SELECT * FROM riders WHERE rider_id = ?", (rider_id,))
    return cursor.fetchone()

def select_riders(cursor):
    team = []
    total_cost = 0
    num_men = 0
    num_women = 0

    while len(team) < TEAM_SIZE:
        display_available_riders(cursor) 

        rider_id = input("\nEnter rider No: ")

        rider = fetch_rider_by_id(cursor, rider_id)  # returns tuple

        # check if rider already in team
        if rider in team:
            print("cant select rider twice")
            input("press enter to continue > ")
            continue

        # Check cost and team size
        if total_cost + rider[2] > TEAM_BUDGET:
            print(f"Rider costs {rider[2]}. You only have {TEAM_BUDGET - total_cost} left.")
            input("press enter to continue > ")
            continue

        # Check gender 
        if rider[3] == 'M' and num_men >= MAX_MEN:
            print("You already have maximum men on your team!")
            continue
        elif rider[3] == 'F' and num_women >= MAX_WOMEN:
            print("You already have maximum women on your team!")
            continue

        # If all checks pass, add rider to team and update totals
        team.append(rider)
        total_cost += rider[2]
        if rider[3] == 'M':
            num_men += 1
        else:
            num_women += 1

        print(f"Added {rider[1]} to your team! Remaining budget: ${TEAM_BUDGET - total_cost}\n")

    print("Team complete!\n")
    print("No.  | Name                 | Cost")
    print("-------------------------------------")
    for i, (rider_id, name, cost, gender) in enumerate(team, start=1):
        print(f"{str(i).ljust(4)} | {name.ljust(25)} | ${cost}")

   
login_or_register(cursor, conn)
select_riders(cursor)

conn.close()
