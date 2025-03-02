from database.database import Database
from authentication.authentication import Authentication


def add_user(username, password, user_type="student"):
    # יצירת חיבור למסד הנתונים
    db = Database()
    auth = Authentication(db)

    try:
        # ניסיון להוספת המשתמש
        success = auth.register_user(username, password, user_type)

        if success:
            print(f"המשתמש {username} נוסף בהצלחה!")
        else:
            print("שם המשתמש כבר תפוס")

    except Exception as e:
        print(f"אירעה שגיאה: {str(e)}")
    finally:
        # סגירת החיבור למסד הנתונים
        db.conn.close()


# דוגמה לשימוש:
if __name__ == "__main__":
    username = input("הכנס שם משתמש: ")
    password = input("הכנס סיסמה: ")
    user_type = input("הכנס סוג משתמש (student/teacher): ")

    add_user(username, password, user_type)


