# הגדרת מחלקת מסד נתונים
class Database:
    def __init__(self):
        # יצירת חיבור למסד נתונים חדש או התחברות לקיים
        self.conn = sqlite3.connect('exam_system.db')
        # יצירת כל הטבלאות הנדרשות
        self.create_tables()
    
    def create_tables(self):
        # יצירת מצביע לביצוע פקודות SQL
        cursor = self.conn.cursor()
        
        # יצירת טבלת משתמשים
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                user_type TEXT
            )
        ''')
        
        # יצירת טבלת מבחנים
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exams (
                exam_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                total_marks INTEGER
            )
        ''')
        
        # יצירת טבלת תוצאות
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS results (
                result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                exam_id INTEGER,
                score INTEGER,
                date_taken DATE,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (exam_id) REFERENCES exams (exam_id)
            )
        ''')
        
        # יצירת טבלת שאלות
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                question_id INTEGER PRIMARY KEY AUTOINCREMENT,
                exam_id INTEGER,
                content TEXT NOT NULL,
                question_type TEXT,  -- 'multiple_choice' או 'open_ended'
                FOREIGN KEY (exam_id) REFERENCES exams (exam_id)
            )
        ''')
        
        # יצירת טבלת אפשרויות תשובה
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS options (
                option_id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER,
                content TEXT NOT NULL,
                is_correct BOOLEAN,
                FOREIGN KEY (question_id) REFERENCES questions (question_id)
            )
        ''')
        
        # יצירת טבלת תשובות של תלמידים
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS student_answers (
                answer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                result_id INTEGER,
                question_id INTEGER,
                student_answer TEXT,
                FOREIGN KEY (result_id) REFERENCES results (result_id),
                FOREIGN KEY (question_id) REFERENCES questions (question_id)
            )
        ''')
        
        # שמירת כל השינויים במסד הנתונים
        self.conn.commit()

    # פונקציה ליצירת גיבוי של מסד הנתונים
    def backup_database(self):
        # יצירת חיבור לקובץ גיבוי חדש
        backup_conn = sqlite3.connect('exam_system_backup.db')
        # העתקת כל הנתונים לקובץ הגיבוי
        with backup_conn:
            self.conn.backup(backup_conn)
        # סגירת החיבור לקובץ הגיבוי
        backup_conn.close()

    # פונקציה לשחזור מסד נתונים מגיבוי
    def restore_database(self, backup_path):
        # יצירת חיבור לקובץ הגיבוי
        backup_conn = sqlite3.connect(backup_path)
        # שחזור הנתונים למסד הנתונים הראשי
        with self.conn:
            backup_conn.backup(self.conn)
        # סגירת החיבור לקובץ הגיבוי
        backup_conn.close()

    # פונקציה לקבלת סטטיסטיקות על מסד הנתונים
    def get_database_stats(self):
        # יצירת מצביע לביצוע פקודות SQL
        cursor = self.conn.cursor()
        # יצירת מילון לאחסון הסטטיסטיקות
        stats = {
            'total_users': 0,
            'total_exams': 0,
            'total_results': 0
        }
        
        # ספירת כמות הרשומות בכל טבלה
        for table, query in [
            ('users', 'SELECT COUNT(*) FROM users'),
            ('exams', 'SELECT COUNT(*) FROM exams'),
            ('results', 'SELECT COUNT(*) FROM results')
        ]:
            # הרצת השאילתה ושמירת התוצאה
            cursor.execute(query)
            stats[f'total_{table}'] = cursor.fetchone()[0]
        
        # החזרת הסטטיסטיקות
        return stats

# הגדרת מחלקת אימות משתמשים
class Authentication:
    def __init__(self, db):
        # קבלת מופע של מסד הנתונים
        self.db = db
    
    # פונקציה להצפנת סיסמאות
    def hash_password(self, password):
        # המרת הסיסמה לפורמט מתאים להצפנה
        return hashlib.sha256(password.encode()).hexdigest()
    
    # פונקציה להרשמת משתמש חדש
    def register_user(self, username, password, user_type="student"):
        # יצירת מצביע לביצוע פקודות SQL
        cursor = self.db.conn.cursor()
        # הצפנת הסיסמה
        hashed_password = self.hash_password(password)
        
        try:
            # הרצת פקודת הוספת משתמש חדש
            cursor.execute('''
                INSERT INTO users (username, password, user_type)
                VALUES (?, ?, ?)
            ''', (username, hashed_password, user_type))
            # שמירת השינויים
            self.db.conn.commit()
            # החזרת הצלחה
            return True
        except sqlite3.IntegrityError:
            # במקרה של שם משתמש כפול
            return False
    
    # פונקציה להתחברות למערכת
    def login(self, username, password):
        # יצירת מצביע לביצוע פקודות SQL
        cursor = self.db.conn.cursor()
        # הצפנת הסיסמה להשוואה
        hashed_password = self.hash_password(password)
        
        # הרצת שאילתה לבדיקת פרטי ההתחברות
        cursor.execute('''
            SELECT * FROM users 
            WHERE username = ? AND password = ?
        ''', (username, hashed_password))
        
        # החזרת פרטי המשתמש אם נמצא
        return cursor.fetchone()

# הגדרת מחלקת ניהול מבחנים
class ExamSystem:
    def __init__(self, db):
        # קבלת מופע של מסד הנתונים
        self.db = db
    
    # פונקציה להוספת מבחן חדש
    def add_exam(self, name, description, total_marks):
        # יצירת מצביע לביצוע פקודות SQL
        cursor = self.db.conn.cursor()
        # הרצת פקודת הוספת מבחן חדש
        cursor.execute('''
            INSERT INTO exams (name, description, total_marks)
            VALUES (?, ?, ?)
        ''', (name, description, total_marks))
        # שמירת השינויים
        self.db.conn.commit()
    
    # פונקציה לקבלת מבחנים זמינים לתלמיד
    def get_available_exams(self, user_id):
        # יצירת מצביע לביצוע פקודות SQL
        cursor = self.db.conn.cursor()
        # הרצת שאילתה שמחזירה רק מבחנים שהתלמיד עדיין לא ביצע
        cursor.execute('''
            SELECT e.*, 
                   (SELECT COUNT(*) FROM results r 
                    WHERE r.exam_id = e.exam_id AND r.user_id = ?) as completed
            FROM exams e
            WHERE e.exam_id NOT IN (
                SELECT exam_id FROM results 
                WHERE user_id = ? AND score IS NOT NULL
            )
            ORDER BY e.exam_id
        ''', (user_id, user_id))
        return cursor.fetchall()
    
    # פונקציה לבדיקה אם התלמיד כבר ביצע מבחן
    def check_exam_status(self, user_id, exam_id):
        # יצירת מצביע לביצוע פקודות SQL
        cursor = self.db.conn.cursor()
        # הרצת שאילתה לבדיקה אם התלמיד כבר ביצע את המבחן
        cursor.execute('''
            SELECT r.result_id, r.score, r.date_taken
            FROM results r
            WHERE r.user_id = ? AND r.exam_id = ?
        ''', (user_id, exam_id))
        return cursor.fetchone()
    
    # פונקציה להזנת תשובות למבחן
    def submit_exam(self, user_id, exam_id, answers):
        # בדיקה אם התלמיד כבר ביצע את המבחן
        if self.check_exam_status(user_id, exam_id):
            raise ValueError("התלמיד כבר ביצע את המבחן הזה")

        # הזנת התוצאה הראשונית
        cursor = self.db.conn.cursor()
        cursor.execute('''
            INSERT INTO results (user_id, exam_id, score, date_taken)
            VALUES (?, ?, ?, ?)
        ''', (user_id, exam_id, None, datetime.now().date()))
        result_id = cursor.lastrowid

        # הזנת התשובות
        question_manager = QuestionManager(self.db)
        score, max_score = question_manager.check_answers(result_id, answers)

        # עדכון הציון הסופי
        cursor.execute('''
            UPDATE results 
            SET score = ? 
            WHERE result_id = ?
        ''', (score, result_id))
        self.db.conn.commit()

        return score, max_score

# הגדרת מחלקת מעקב ציונים
class GradeTracker:
    def __init__(self, db):
        # קבלת מופע של מסד הנתונים
        self.db = db
    
    # פונקציה להשוואת תלמיד מול הכיתה
    def compare_student_to_class(self, user_id):
        # יצירת מצביע לביצוע פקודות SQL
        cursor = self.db.conn.cursor()
        # הרצת שאילתה מורכבת להשוואת ביצועים
        cursor.execute('''
            SELECT 
                e.name as exam_name,
                r.score as student_score,
                (SELECT AVG(score) FROM results WHERE exam_id = e.exam_id) as class_average,
                (SELECT COUNT(*) FROM results WHERE exam_id = e.exam_id) as class_size
            FROM results r
            JOIN exams e ON r.exam_id = e.exam_id
            WHERE r.user_id = ?
            ORDER BY r.date_taken DESC
        ''', (user_id,))
        return cursor.fetchall()

# הגדרת מחלקת ניהול שאלות
class QuestionManager:
    def __init__(self, db):
        # קבלת מופע של מסד הנתונים
        self.db = db
    
    # פונקציה להוספת שאלה חדשה למבחן
    def add_question(self, exam_id, content, question_type='multiple_choice'):
        # יצירת מצביע לביצוע פקודות SQL
        cursor = self.db.conn.cursor()
        # הרצת פקודת הוספת שאלה חדשה
        cursor.execute('''
            INSERT INTO questions (exam_id, content, question_type)
            VALUES (?, ?, ?)
        ''', (exam_id, content, question_type))
        self.db.conn.commit()
        return cursor.lastrowid
    
    # פונקציה להוספת אפשרויות תשובה לשאלה
    def add_options(self, question_id, options, correct_index):
        # יצירת מצביע לביצוע פקודות SQL
        cursor = self.db.conn.cursor()
        # הוספת כל האפשרויות עם סימון התשובה הנכונה
        for i, option in enumerate(options):
            is_correct = (i == correct_index)
            cursor.execute('''
                INSERT INTO options (question_id, content, is_correct)
                VALUES (?, ?, ?)
            ''', (question_id, option, is_correct))
        self.db.conn.commit()
    
    # פונקציה לקבלת כל השאלות והאפשרויות למבחן
    def get_exam_questions(self, exam_id):
        # יצירת מצביע לביצוע פקודות SQL
        cursor = self.db.conn.cursor()
        # הרצת שאילתה שמחזירה את כל השאלות והאפשרויות
        cursor.execute('''
            SELECT q.question_id, q.content, q.question_type
            FROM questions q
            WHERE q.exam_id = ?
            ORDER BY q.question_id
        ''', (exam_id,))
        questions = cursor.fetchall()
        
        # הוספת האפשרויות לכל שאלה
        for question in questions:
            cursor.execute('''
                SELECT option_id, content, is_correct
                FROM options
                WHERE question_id = ?
                ORDER BY option_id
            ''', (question[0],))
            question += (cursor.fetchall(),)
        
        return questions
    
    # פונקציה לבדיקת תשובות של תלמיד
    def check_answers(self, result_id, answers):
        # יצירת מצביע לביצוע פקודות SQL
        cursor = self.db.conn.cursor()
        total_score = 0
        max_score = 0
        
        # בדיקת כל התשובות
        for question_id, student_answer in answers:
            # בדיקה אם זו שאלת בחירה מרובה או שאלה פתוחה
            cursor.execute('''
                SELECT q.question_type, o.is_correct
                FROM questions q
                JOIN options o ON q.question_id = o.question_id
                WHERE q.question_id = ?
            ''', (question_id,))
            question_data = cursor.fetchone()
            
            if question_data[0] == 'multiple_choice':
                # בדיקת תשובה לשאלת בחירה מרובה
                is_correct = question_data[1]
                if is_correct:
                    total_score += 1
                max_score += 1
            else:
                # טיפול בשאלה פתוחה - כרגע מעריכים ידנית
                max_score += 1
        
        # שמירת התשובות
        for question_id, student_answer in answers:
            cursor.execute('''
                INSERT INTO student_answers (result_id, question_id, student_answer)
                VALUES (?, ?, ?)
            ''', (result_id, question_id, student_answer))
        
        self.db.conn.commit()
        return total_score, max_score

# פונקציית main להדגמת השימוש
def main():
    # יצירת מופע של מסד הנתונים
    db = Database()
    
    # יצירת מופעים של המחלקות
    auth = Authentication(db)
    exam_system = ExamSystem(db)
    grade_tracker = GradeTracker(db)
    question_manager = QuestionManager(db)
    
    # הרשמת משתמש חדש
    auth.register_user("student1", "password123")
    
    # התחברות
    user = auth.login("student1", "password123")
    
    # הוספת מבחן חדש
    exam_id = exam_system.add_exam("מבחן בסיסי", "מבחן בסיסי בפייתון", 100)
    
    # הוספת שאלת בחירה מרובה
    question_id = question_manager.add_question(
        exam_id,
        "מהי הפונקציה הראשית בפייתון?",
        "multiple_choice"
    )
    question_manager.add_options(
        question_id,
        ["def main():", "public static void main()", "function start()", "void main()"],
        0  # האפשרות הנכונה היא הראשונה
    )
    
    # הוספת שאלה פתוחה
    question_id = question_manager.add_question(
        exam_id,
        "הסבר מהם משתנים בפייתון",
        "open_ended"
    )
    
    # הצגת המבחן
    questions = question_manager.get_exam_questions(exam_id)
    print("המבחן:")
    for question in questions:
        print(f"\nשאלה {question[0]} ({question[2]}):")
        print(question[1])
        if question[2] == 'multiple_choice':
            for option in question[3]:
                print(f"{option[0]}. {option[1]}")
    
    # ניסיון לביצוע המבחן
    try:
        # קבלת השאלות
        questions = question_manager.get_exam_questions(1)
        
        # הזנת תשובות
        answers = [
            (1, "0"),  # תשובה לשאלת בחירה מרובה
            (2, "משתנים הם מקומות אחסון בזיכרון...")  # תשובה לשאלה פתוחה
        ]
        
        # ביצוע המבחן
        score, max_score = exam_system.submit_exam(user[0], 1, answers)
        print(f"\nציון: {score}/{max_score}")
        
    except ValueError as e:
        print(f"שגיאה: {e}")

if __name__ == "__main__":
    main()
