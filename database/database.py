import sqlite3
from datetime import datetime


class Database:
    def __init__(self):
        self.conn = sqlite3.connect('exam_system.db')
        self.create_tables()

    def create_tables(self):
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
                question_type TEXT,
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

        self.conn.commit()

    def backup_database(self):
        backup_conn = sqlite3.connect('exam_system_backup.db')
        with backup_conn:
            self.conn.backup(backup_conn)
        backup_conn.close()

    def restore_database(self, backup_path):
        backup_conn = sqlite3.connect(backup_path)
        with self.conn:
            backup_conn.backup(self.conn)
        backup_conn.close()

    def get_database_stats(self):
        cursor = self.conn.cursor()
        stats = {
            'total_users': 0,
            'total_exams': 0,
            'total_results': 0
        }

        for table, query in [
            ('users', 'SELECT COUNT(*) FROM users'),
            ('exams', 'SELECT COUNT(*) FROM exams'),
            ('results', 'SELECT COUNT(*) FROM results')
        ]:
            cursor.execute(query)
            stats[f'total_{table}'] = cursor.fetchone()[0]

        return stats
