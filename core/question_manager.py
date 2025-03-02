from database.database import Database


class QuestionManager:
    def __init__(self, db):
        self.db = db

    def add_question(self, exam_id, content, question_type='multiple_choice'):
        cursor = self.db.conn.cursor()
        cursor.execute('''
            INSERT INTO questions (exam_id, content, question_type)
            VALUES (?, ?, ?)
        ''', (exam_id, content, question_type))
        self.db.conn.commit()
        return cursor.lastrowid

    def add_options(self, question_id, options, correct_index):
        cursor = self.db.conn.cursor()
        for i, option in enumerate(options):
            is_correct = (i == correct_index)
            cursor.execute('''
                INSERT INTO options (question_id, content, is_correct)
                VALUES (?, ?, ?)
            ''', (question_id, option, is_correct))
        self.db.conn.commit()

    def get_exam_questions(self, exam_id):
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT q.question_id, q.content, q.question_type
            FROM questions q
            WHERE q.exam_id = ?
            ORDER BY q.question_id
        ''', (exam_id,))
        questions = cursor.fetchall()

        for question in questions:
            cursor.execute('''
                SELECT option_id, content, is_correct
                FROM options
                WHERE question_id = ?
                ORDER BY option_id
            ''', (question[0],))
            question += (cursor.fetchall(),)

        return questions

    def check_answers(self, result_id, answers):
        cursor = self.db.conn.cursor()
        total_score = 0
        max_score = 0

        for question_id, student_answer in answers:
            cursor.execute('''
                SELECT q.question_type, o.is_correct
                FROM questions q
                JOIN options o ON q.question_id = o.question_id
                WHERE q.question_id = ?
            ''', (question_id,))
            question_data = cursor.fetchone()

            if question_data[0] == 'multiple_choice':
                is_correct = question_data[1]
                if is_correct:
                    total_score += 1
                max_score += 1
            else:
                max_score += 1

        for question_id, student_answer in answers:
            cursor.execute('''
                INSERT INTO student_answers (result_id, question_id, student_answer)
                VALUES (?, ?, ?)
            ''', (result_id, question_id, student_answer))

        self.db.conn.commit()
        return total_score, max_score
