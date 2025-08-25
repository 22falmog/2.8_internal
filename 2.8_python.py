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
            tutorial()
            return user
        else:
            print("Invalid input. Please enter 1 or 2.")

def update_rider_results(cursor, conn):
    from datetime import datetime

    # Step 1: Show upcoming or unscored races
    cursor.execute("SELECT id, location, date FROM races ORDER BY date")
    races = cursor.fetchall()

    if not races:
        print("No races found.")
        return

    print("\nAvailable races:")
    for i, (race_id, location, date) in enumerate(races, start=1):
        race_date = datetime.strptime(date, "%Y-%m-%d").date()
        status = "Upcoming" if race_date >= datetime.today().date() else "Completed"
        print(f"{i}. {location} ({date}) - {status}")

    choice = input("\nEnter the number of the race to enter results for: ").strip()
    if not choice.isdigit() or int(choice) < 1 or int(choice) > len(races):
        print("Invalid selection.\n")
        return

    race_id, location, date = races[int(choice) - 1]
    print(f"\nEntering results for {location} ({date})\n")

    # Step 2: Get all riders
    cursor.execute("SELECT rider_id, name FROM riders ORDER BY name")
    riders = cursor.fetchall()

    for rider_id, name in riders:
        while True:
            points_input = input(f"Enter points earned by {name} (or 'skip'): ").strip()
            if points_input.lower() == "skip":
                break
            if not points_input.isdigit():
                print("Invalid input. Enter a whole number or 'skip'.")
                continue
            points = int(points_input)
            
            # Insert or update rider_results table
            cursor.execute("""
                INSERT INTO rider_results (race_id, rider_id, points)
                VALUES (?, ?, ?)
                ON CONFLICT(race_id, rider_id) DO UPDATE SET points = excluded.points
            """, (race_id, rider_id, points))
            conn.commit()
            break

    print("\nAll rider results entered for this race.")

    # Step 3: Update user race scores
    update_user_race_scores(cursor, conn, race_id)
    print("User race scores updated.\n")


def admin_menu(cursor, conn):
    while True:
        print("\n--- Admin Panel ---")
        print("1. Update rider points and race scores")
        print("2. commit results to leaderboard")
        print("3. Exit admin panel")

        choice = input("Enter your choice: ").strip()

        if choice == '1':
            # Show all races
            cursor.execute("SELECT id, date, location FROM races ORDER BY date")
            races = cursor.fetchall()

            if not races:
                print("No races found.")
                continue

            print("\nSelect a race to update:")
            for i, (race_id, date, location) in enumerate(races, start=1):
                print(f"{i}. {location} on {date}")

            race_choice = input("Enter the number of the race: ").strip()
            if not race_choice.isdigit() or int(race_choice) < 1 or int(race_choice) > len(races):
                print("Invalid selection.")
                continue

            race_id = races[int(race_choice) - 1][0]

            # Update rider points
            update_rider_results(cursor, conn)

            # Update user scores for this race
            update_user_race_scores(cursor, conn, race_id)

            print(f"User scores updated for race ID {race_id}.\n")
        
        elif choice == '2':
            # Show all races
            cursor.execute("SELECT id, date, location FROM races ORDER BY date")
            races = cursor.fetchall()

            if not races:
                print("No races found.")
                continue

            print("\nSelect a race to commit to leaderboard:")
            for i, (race_id, date, location) in enumerate(races, start=1):
                print(f"{i}. {location} on {date}")

            race_choice = input("Enter the number of the race: ").strip()
            if not race_choice.isdigit() or int(race_choice) < 1 or int(race_choice) > len(races):
                print("Invalid selection.")
                continue

            race_id = races[int(race_choice) - 1][0]

            update_user_race_scores(cursor, conn, race_id)
            print(f"Leaderboard updated for race ID {race_id}.")

        elif choice == '3':
            print("Exiting admin panel...\n")
            break
        else:
            print("Invalid option. Please enter 1 or 2.")


def display_available_riders(cursor, team, remaining_budget, num_men, num_women, gender_filter=None):
    selected_ids = [rider[0] for rider in team]

    # Adjust query based on gender
    if gender_filter in ('M', 'F'):
        cursor.execute("SELECT rider_id, name, cost, gender, points FROM riders WHERE gender = ?", (gender_filter,))
    else:
        cursor.execute("SELECT rider_id, name, cost, gender, points FROM riders")
    
    all_riders = cursor.fetchall()
    
    print("No.  | Name                         | Cost      | Points   | Gender | Status")
    print("-------------------------------------------------------------------------------")
   
    display_number = 1
    display_map = {}

    for rider_id, name, cost, gender, points in all_riders:
        if rider_id in selected_ids:
            continue

        too_expensive = cost > remaining_budget
        gender_limit_reached = (gender == 'M' and num_men >= MAX_MEN) or (gender == 'F' and num_women >= MAX_WOMEN)

        label = ""
        color_start = ""
        color_end = ""

        if too_expensive or gender_limit_reached:
            label = "(Too expensive)" if too_expensive else "(Gender full)"
            color_start = "\033[91m"
            color_end = "\033[0m"

        print(f"{color_start}{str(display_number).ljust(4)} | {name.ljust(28)} | ${str(cost).ljust(8)} | {str(points).ljust(8)} | {gender}     | {label}{color_end}")

        display_map[display_number] = rider_id
        display_number += 1

    return display_map


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

def view_team(cursor, user, team=None):

    if team is None:
        team = load_user_team(cursor, user[0])

    if not team:
        print("You don't have a team yet. Build one first!")
        return

    total_cost = sum(rider[2] for rider in team)
    sorted_team = sorted(team, key=lambda rider: (rider[3] == 'F', -rider[4]))

    print(f"\n{user[1]}'s Fantasy Team:\n")
    print("No.  | Name                  | Cost     | Points   | Gender")
    print("---------------------------------------------------------------")
    for i, (rider_id, name, cost, gender, points) in enumerate(sorted_team, start=1):
        print(f"{str(i).ljust(4)} | {name.ljust(20)} | ${str(cost).ljust(8)} | {str(points).ljust(8)} | {gender}")
    print(f"\nTotal team cost: ${total_cost}")


def display_team_status(team, total_cost, num_men, num_women):
    # Progress bar
    team_slots = ['■' if i < len(team) else '□' for i in range(TEAM_SIZE)]
    progress = ' '.join(team_slots)
    print("\n--- Your Team Status ---")
    print(f"Team: {len(team)}/{TEAM_SIZE} | {progress}")
    print(f"Budget remaining: ${TEAM_BUDGET - total_cost}")
    print(f"Men: {num_men}/{MAX_MEN} | Women: {num_women}/{MAX_WOMEN}")
    print("------------------------\n")

def add_male_rider(cursor, team, total_cost, num_men, num_women):
    if num_men >= MAX_MEN:
        print("\n⚠️ You already have the maximum number of male riders ({}).".format(MAX_MEN))
        print("Delete a male rider before adding another.\n")
        return None, total_cost, num_men, num_women

    remaining_budget = TEAM_BUDGET - total_cost
    display_map = display_available_riders(cursor, team, remaining_budget, num_men, num_women, gender_filter='M')

    if not display_map:
        print("No available male riders to select.\n")
        return None, total_cost, num_men, num_women

    rider_number = input("\nEnter the number of the male rider to add (or press Enter to cancel): ").strip()

    if rider_number == "":
        print("Cancelled.\n")
        return None, total_cost, num_men, num_women

    if not rider_number.isdigit() or int(rider_number) not in display_map:
        print("Invalid selection.\n")
        return None, total_cost, num_men, num_women
    rider_id = display_map[int(rider_number)]
    rider = fetch_rider_by_id(cursor, rider_id)

    if rider in team:
        print("Can't select the same rider twice.\n")
        return None, total_cost, num_men, num_women

    if total_cost + rider[2] > TEAM_BUDGET:
        print(f"Rider costs ${rider[2]}, you only have ${TEAM_BUDGET - total_cost} left.\n")
        return None, total_cost, num_men, num_women

    if num_men >= MAX_MEN:
        print("You already have the maximum number of men.\n")
        return None, total_cost, num_men, num_women

    team.append(rider)
    total_cost += rider[2]
    num_men += 1
    print(f"Added {rider[1]} to your team!\n")
    return rider, total_cost, num_men, num_women


def add_female_rider(cursor, team, total_cost, num_men, num_women):
    if num_women >= MAX_WOMEN:
        print("\n⚠️ You already have the maximum number of female riders ({}).".format(MAX_WOMEN))
        print("Delete a female rider before adding another.\n")
        return None, total_cost, num_men, num_women
 
    remaining_budget = TEAM_BUDGET - total_cost
    display_map = display_available_riders(cursor, team, remaining_budget, num_men, num_women, gender_filter='F')

    if not display_map:
        print("No available female riders to select.\n")
        return None, total_cost, num_men, num_women

    rider_number = input("\nEnter the number of the female rider to add (or press enter to cancel): ").strip()

    if rider_number == "":
        print("Cancelled.\n")
        return None, total_cost, num_men, num_women

    if not rider_number.isdigit() or int(rider_number) not in display_map:
        print("Invalid selection.\n")
        return None, total_cost, num_men, num_women
    rider_id = display_map[int(rider_number)]
    rider = fetch_rider_by_id(cursor, rider_id)

    if rider in team:
        print("Can't select the same rider twice.\n")
        return None, total_cost, num_men, num_women

    if total_cost + rider[2] > TEAM_BUDGET:
        print(f"Rider costs ${rider[2]}, you only have ${TEAM_BUDGET - total_cost} left.\n")
        return None, total_cost, num_men, num_women

    if num_women >= MAX_WOMEN:
        print("You already have the maximum number of women.\n")
        return None, total_cost, num_men, num_women

    team.append(rider)
    total_cost += rider[2]
    num_women += 1
    print(f"Added {rider[1]} to your team!\n")
    return rider, total_cost, num_men, num_women


def delete_rider(team, total_cost, num_men, num_women, cursor, user):
    if not team:
        print("Your team is empty.\n")
        return total_cost, num_men, num_women

    # Display team using view_team style
    view_team(cursor, user, team)

    choice = input("\nEnter the number of the rider to remove: ").strip()
    if not choice.isdigit() or int(choice) < 1 or int(choice) > len(team):
        print("Invalid selection.\n")
        return total_cost, num_men, num_women

    rider = team.pop(int(choice) - 1)
    total_cost -= rider[2]
    if rider[3] == 'M':
        num_men -= 1
    else:
        num_women -= 1

    print(f"Removed {rider[1]} from your team.\n")
    return total_cost, num_men, num_women


def build_team(cursor, conn, user):
    # Load existing team if any
    existing_team = load_user_team(cursor, user[0])
    if existing_team:
        print("\nPlease delete your existing team before creating a new one.")
        input("Press Enter to return to the menu.")
        return

    team = []
    total_cost = 0
    num_men = 0
    num_women = 0

    while len(team) < TEAM_SIZE:
        display_team_status(team, total_cost, num_men, num_women)
        print("Options:")
        print("1. Add Male Rider")
        print("2. Add Female Rider")
        print("3. Delete a Rider")
        print("4. Exit Team Builder")

        choice = input("\nEnter your choice: ").strip()

        if choice == '1':
            rider, total_cost, num_men, num_women = add_male_rider(cursor, team, total_cost, num_men, num_women)
        elif choice == '2':
            rider, total_cost, num_men, num_women = add_female_rider(cursor, team, total_cost, num_men, num_women)
        elif choice == '3':
            total_cost, num_men, num_women = delete_rider(team, total_cost, num_men, num_women, cursor, user)
        elif choice == '4':
            print("Exiting team builder.\n")
            return
        else:
            print("Invalid choice.\n")
            continue

    # Save completed team
    save_user_team(cursor, conn, user[0], team)
    print("Team complete!\n")
    view_team(cursor, user)


def delete_team(cursor, conn, user):
    confirm = input("\nAre you sure you want to delete your entire team? (Press 1 to confirm, 2 to cancel): ").strip()

    if confirm != "1":
        print("\nTeam deletion cancelled.\n")
        return

    cursor.execute("DELETE FROM user_teams WHERE user_id = ?", (user[0],))
    conn.commit()
    print("\nYour team has been deleted.\n")


def view_leaderboard(cursor):
    cursor.execute("""
        SELECT u.username, SUM(s.points) as total_points
        FROM user_race_scores s
        JOIN users u ON u.user_id = s.user_id
        GROUP BY s.user_id
        ORDER BY total_points DESC
    """)
    for username, points in cursor.fetchall():
        print(f"{username}: {points} points")


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

def tutorial():
    sections = [
        """
Welcome to Fantasy MTB!
Your goal is to build the best team within your budget and finish the season with the most points.
        """,

        """
TEAM CREATION:
- Budget Limit: You have a fixed budget of 1.5 million to spend on riders.
- Team Size: You must fill all 6 spots in your team.
- Gender Rules: You must have 4 male, and 2 female riders in your team.
- Costs: Each rider has a unique cost, so choose wisely to balance talent and budget.
        """,

        """
SCORING:
- Riders earn points based on their real-life race result.
- Your total score is the points your riders earned in races while they were on your team, added together.
        """,

        """
LEADERBOARDS:
- Shows the top players and their scores.
- Updates after each event or scoring period.
- Ties are broken by total budget spent (less spent wins).
        """,

        """
TIPS:
- Watch your budget — once it's gone, you can't add more riders.
- Balance proven riders with potential rising stars.
- Keep an eye on your competitors' scores.
        """
    ]

    for section in sections:
        print("")
        print(section.strip())
        input("\nPress Enter to continue > ")


def update_user_race_scores(cursor, conn, race_id):
    """
    After a race is completed, calculate and store points for each user.
    """

    # Get rider results for this race
    cursor.execute("""
        SELECT rider_id, points
        FROM rider_results
        WHERE race_id = ?
    """, (race_id,))
    race_results = dict(cursor.fetchall())  # {rider_id: points}

    # Get all users
    cursor.execute("SELECT DISTINCT user_id FROM user_teams")
    users = [row[0] for row in cursor.fetchall()]

    for user_id in users:
        # Get the riders in this user's team for the race
        cursor.execute("""
            SELECT rider_id
            FROM user_teams
            WHERE user_id = ?
        """, (user_id,))
        team_riders = [row[0] for row in cursor.fetchall()]

        # Sum points for this user's riders
        total_points = sum(race_results.get(rider_id, 0) for rider_id in team_riders)

        # Insert into user_race_scores
        cursor.execute("""
            INSERT INTO user_race_scores (user_id, race_id, points)
            VALUES (?, ?, ?)
        """, (user_id, race_id, total_points))

    conn.commit()



def user_menu(cursor, conn, user):
    while True:
        print("\n--- FinnBike Fantasy Menu ---\n")
        print("1. Build Your Team")
        print("2. View Your Team")
        print("3. Delete Your Team")
        print("4. View Leaderboard")
        print("5. View Upcoming Races")
        print("6. view tutorial")
        print("7. Log Out\n")

        choice = input("Select an option (1-5): ").strip()

        if choice == '1':
            build_team(cursor, conn, user)
        elif choice == '2':
            view_team(cursor, user)
        elif choice == '3':
            delete_team(cursor, conn, user)
        elif choice == '4':
            view_leaderboard(cursor)
        elif choice == '5':
            display_race_calendar(cursor)
        elif choice == '6':
            tutorial()
        elif choice == '7':
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