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

def update_rider_points(cursor, conn):
    print("\n--- Admin: Update Rider Points ---")

    cursor.execute("SELECT rider_id, name, points FROM riders ORDER BY gender, points DESC")

    riders = cursor.fetchall()

    updated_ids = set()

    for rider_id, name, current_points in riders:
        if rider_id in updated_ids:
            continue

        print(f"\n{name} (Current points: {current_points})")
        response = input("Enter new points, or type 'skip' or 'exit': ").strip()

        if response.lower() == 'exit':
            print("Exiting update session.")
            break
        elif response.lower() == 'skip':
            continue

        if not response.isdigit():
            print("Invalid input. Points must be a whole number.")
            continue

        new_points = int(response)
        cursor.execute("UPDATE riders SET points = ? WHERE rider_id = ?", (new_points, rider_id))
        conn.commit()
        updated_ids.add(rider_id)
        print(f"{name}'s points updated to {new_points}.")

def admin_menu(cursor, conn):
    while True:
        print("\n--- Admin Panel ---")
        print("1. Update rider points")
        print("2. Exit admin panel")

        choice = input("Enter your choice: ")

        if choice == '1':
            update_rider_points(cursor, conn)
        elif choice == '2':
            print("Exiting admin panel...\n")
            break
        else:
            print("Invalid option. Please enter 1 or 2.")

def user_menu(cursor, conn, user):
    while True:
        print("\n--- User Menu ---")
        print("1. Build Your Team")
        print("2. View Your Team")
        print("3. Delete Your Team")
        print("4. View Leaderboard")
        print("5. Log Out")

        choice = input("Select an option (1-5): ").strip()

        if choice == '1':
            print("Team building not yet connected.")  # replace with your function later
        elif choice == '2':
            print("Team viewing coming soon.")  # replace with view_team(user) later
        elif choice == '3':
            print("Delete team function not yet ready.")  # hook in later
        elif choice == '4':
            print("Leaderboard not built yet.")  # future function
        elif choice == '5':
            print("Logging out...\n")
            break
        else:
            print("Invalid option. Please enter a number between 1 and 5.")


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
    for i, (rider_id, name, cost, gender, points) in enumerate(team, start=1):
        print(f"{str(i).ljust(4)} | {name.ljust(25)} | ${cost}")
    print(f"\nRemaining budget: ${TEAM_BUDGET - total_cost}\n")

def main():
    while True:
        user = login_or_register(cursor, conn)

        if user[3] == 1:  # is_admin
            print("logged in as admin")
            admin_menu(cursor, conn)
        else:
            user_menu(cursor, conn, user)
        
        print("\nyou have been logged out\n")

main()


conn.close()
