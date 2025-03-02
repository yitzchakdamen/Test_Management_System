from database.database import Database


class GradeTracker:
    def __init__(self, db):
        self.db = db

    def compare_student_to_class(self, user_id):
        cursor = self.db.conn.cursor()
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
