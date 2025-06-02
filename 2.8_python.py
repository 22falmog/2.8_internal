import sqlite3
conn = sqlite3.connect('fantasy.DB')
cursor = conn.cursor()

def display_all_riders(cursor):
    cursor.execute("SELECT name, cost FROM riders")
    riders = cursor.fetchall()

    print("No.  | Name                 | Cost")
    print("-------------------------------------")
    for i, (name, cost) in enumerate(riders, start=1):
        print(f"{str(i).ljust(4)} | {name.ljust(20)} | ${cost}")





conn.close()