TEAM_BUDGET = 1500000
TEAM_SIZE = 6
MAX_MEN = 4
MAX_WOMEN = 2

import sqlite3
conn = sqlite3.connect('fantasy.DB')
cursor = conn.cursor()

def display_all_riders(cursor):
    cursor.execute("SELECT name, cost FROM riders")
    riders = cursor.fetchall()

    print("No.  | Name                 | Cost")
    print("-------------------------------------")
    for i, (name, cost) in enumerate(riders, start=1):
        print(f"{str(i).ljust(4)} | {name.ljust(25)} | ${cost}")



display_all_riders(cursor)

conn.close()