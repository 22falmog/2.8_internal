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

def display_available_riders(cursor, team):
    selected_ids = [rider[0] for rider in team]

    cursor.execute("SELECT rider_id, name, cost FROM riders")
    all_riders = cursor.fetchall()

    print("No.  | Name                 | Cost")
    print("-------------------------------------")
    for i, (rider_id, name, cost) in enumerate(all_riders, start=1):
        if rider_id not in selected_ids:
            print(f"{str(i).ljust(4)} | {name.ljust(25)} | ${cost}")


def fetch_rider_by_id(cursor, rider_id):
    cursor.execute("SELECT * FROM riders WHERE rider_id = ?", (rider_id,))
    return cursor.fetchone()

def save_user_team(cursor, conn, user_id, team):
    # Remove old team for user
    cursor.execute("DELETE FROM user_teams WHERE user_id = ?", (user_id,))
    # Insert new team
    for rider in team:
        rider_id = rider[0]  # rider_id is first element
        cursor.execute("INSERT INTO user_teams (user_id, rider_id) VALUES (?, ?)", (user_id, rider_id))
    conn.commit()
    print("Team saved successfully!")

def load_user_team(cursor, user_id):
    cursor.execute("""
        SELECT r.rider_id, r.name, r.cost, r.gender, r.points
        FROM riders r
        JOIN user_teams ut ON r.rider_id = ut.rider_id
        WHERE ut.user_id = ?
    """, (user_id,))
    return cursor.fetchall()

def select_riders(cursor, conn, user):
    team = []
    total_cost = 0
    num_men = 0
    num_women = 0

    while len(team) < TEAM_SIZE:
        display_available_riders(cursor, team)

        rider_id = input("\nEnter rider ID: ").strip()

        if not rider_id.isdigit():
            print("Please enter a valid number.")
            continue

        rider = fetch_rider_by_id(cursor, int(rider_id))
        if not rider:
            print("Rider not found.")
            continue

        # check if rider already in team
        if rider in team:
            print("Can't select rider twice.")
            input("Press Enter to continue > ")
            continue

        # Check cost and team size
        if total_cost + rider[2] > TEAM_BUDGET:
            print(f"Rider costs {rider[2]}. You only have ${TEAM_BUDGET - total_cost} left.")
            input("Press Enter to continue > ")
            continue

        # Check gender
        if rider[3] == 'M' and num_men >= MAX_MEN:
            print("You already have maximum men on your team!")
            continue
        elif rider[3] == 'F' and num_women >= MAX_WOMEN:
            print("You already have maximum women on your team!")
            continue

        # Add rider to team and update totals
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

    # Save team to DB
    save_user_team(cursor, conn, user[0], team)

def view_team(cursor, user):
    team = load_user_team(cursor, user[0])
    if not team:
        print("You don't have a team yet. Build one first!")
        return

    total_cost = sum(rider[2] for rider in team)

    print("Your Team:\n")
    print("No.  | Name                 | Cost")
    print("-------------------------------------")
    for i, (rider_id, name, cost, gender, points) in enumerate(team, start=1):
        print(f"{str(i).ljust(4)} | {name.ljust(25)} | ${cost}")
    print(f"\nTotal team cost: ${total_cost}")

def delete_team(cursor, conn, user):
    cursor.execute("DELETE FROM user_teams WHERE user_id = ?", (user[0],))
    conn.commit()
    print("Your team has been deleted.")

from datetime import datetime

def show_race_calendar(cursor):
    from datetime import datetime

def display_race_calendar(cursor):
    cursor.execute("SELECT date, location FROM races ORDER BY date")
    races = cursor.fetchall()

    print("Location".ljust(25), "Date".ljust(15), "Status")
    print(50 * "-")

    today = datetime.today().date()

    for date, location in races:
        race_date = datetime.strptime(date, "%Y-%m-%d").date()

        if race_date >= today:
            status = "\033[92m(upcoming)\033[0m"  # green
        else:
            status = "\033[91m(past)\033[0m"      # red

        print(location.ljust(25), date.ljust(15), status)


def user_menu(cursor, conn, user):
    while True:
        print("\n--- User Menu ---")
        print("1. Build Your Team")
        print("2. View Your Team")
        print("3. Delete Your Team")
        print("4. View Leaderboard")
        print("5. View Upcoming Races")
        print("6. Log Out")

        choice = input("Select an option (1-5): ").strip()

        if choice == '1':
            select_riders(cursor, conn, user)
        elif choice == '2':
            view_team(cursor, user)
        elif choice == '3':
            delete_team(cursor, conn, user)
        elif choice == '4':
            print("Leaderboard not built yet.")  # future function
        elif choice == '5':
            display_race_calendar(cursor)
        elif choice == '6':
            print("Logging out...\n")
            break
        else:
            print("Invalid option. Please enter a number between 1 and 5.")

def main():
    while True:
        user = login_or_register(cursor, conn)

        if user[3] == 1:  # is_admin
            print("Logged in as admin")
            admin_menu(cursor, conn)
        else:
            user_menu(cursor, conn, user)

        print("\nYou have been logged out\n")

main()

conn.close()