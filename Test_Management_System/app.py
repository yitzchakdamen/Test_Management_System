
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
