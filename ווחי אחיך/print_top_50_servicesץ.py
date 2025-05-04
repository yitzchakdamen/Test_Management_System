
import sqlite3
from tabulate import tabulate

def print_first_50_rows(db_path, table_name):
    try:
        # התחברות למסד הנתונים
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # ביצוע השאילתה
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 50")
        rows = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]

        # הדפסת הנתונים בטבלה יפה
        print(tabulate(rows, headers=column_names, tablefmt="fancy_grid"))

    except sqlite3.Error as e:
        print(f"שגיאה במסד הנתונים: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    db_path = 'db.db'  # שנה לפי הצורך
    table_name = 'people'  # שנה לפי הצורך
    print_first_50_rows(db_path, table_name)
    
    