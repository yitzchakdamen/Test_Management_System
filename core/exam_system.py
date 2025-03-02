from datetime import datetime
from database.database import Database


class ExamSystem:
    def __init__(self, db):
        self.db = db

    def add_exam(self, name, description, total_marks):
        cursor = self.db.conn.cursor()
        cursor.execute('''
            INSERT INTO exams (name, description, total_marks)
            VALUES (?, ?, ?)
        ''', (name, description, total_marks))
        self.db.conn.commit()
        return cursor.lastrowid

    def get_available_exams(self, user_id):
        cursor = self.db.conn.cursor()
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

    def check_exam_status(self, user_id, exam_id):
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT r.result_id, r.score, r.date_taken
            FROM results r
            WHERE r.user_id = ? AND r.exam_id = ?
        ''', (user_id, exam_id))
        return cursor.fetchone()

    def submit_exam(self, user_id, exam_id, answers):
        if self.check_exam_status(user_id, exam_id):
            raise ValueError("התלמיד כבר ביצע את המבחן הזה")

        cursor = self.db.conn.cursor()
        cursor.execute('''
            INSERT INTO results (user_id, exam_id, score, date_taken)
            VALUES (?, ?, ?, ?)
        ''', (user_id, exam_id, None, datetime.now().date()))
        result_id = cursor.lastrowid

        question_manager = QuestionManager(self.db)
        score, max_score = question_manager.check_answers(result_id, answers)

        cursor.execute('''
            UPDATE results 
            SET score = ? 
            WHERE result_id = ?
        ''', (score, result_id))
        self.db.conn.commit()

        return score, max_score
