from flask import Flask, jsonify, request
from authentication.authentication import Authentication
from database.database import Database
from core.exam_system import ExamSystem
from core.grade_tracker import GradeTracker
from core.question_manager import QuestionManager

app = Flask(__name__)

# יצירת מופעים של המחלקות העיקריות
db = Database()
auth = Authentication(db)
exam_system = ExamSystem(db)
grade_tracker = GradeTracker(db)
question_manager = QuestionManager(db)

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    success = auth.register_user(data['username'], data['password'])
    return jsonify({'success': success})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = auth.login(data['username'], data['password'])
    return jsonify({'user': user})

@app.route('/api/exams', methods=['POST'])
def add_exam():
    data = request.json
    exam_id = exam_system.add_exam(
        data['name'],
        data['description'],
        data['total_marks']
    )
    return jsonify({'exam_id': exam_id})

@app.route('/api/exams/<int:exam_id>/questions', methods=['POST'])
def add_question(exam_id):
    data = request.json
    question_id = question_manager.add_question(
        exam_id,
        data['content'],
        data['question_type']
    )
    return jsonify({'question_id': question_id})

@app.route('/api/exams/<int:exam_id>/questions/<int:question_id>/options', methods=['POST'])
def add_options(exam_id, question_id):
    data = request.json
    question_manager.add_options(
        question_id,
        data['options'],
        data['correct_index']
    )
    return jsonify({'status': 'success'})

@app.route('/api/exams/<int:exam_id>/submit', methods=['POST'])
def submit_exam(exam_id):
    data = request.json
    score, max_score = exam_system.submit_exam(
        data['user_id'],
        exam_id,
        data['answers']
    )
    return jsonify({'score': score, 'max_score': max_score})

@app.route('/api/exams/<int:exam_id>/questions', methods=['GET'])
def get_exam_questions(exam_id):
    questions = question_manager.get_exam_questions(exam_id)
    return jsonify({'questions': questions})

@app.route('/api/users/<int:user_id>/stats', methods=['GET'])
def get_user_stats(user_id):
    stats = grade_tracker.compare_student_to_class(user_id)
    return jsonify({'stats': stats})

if __name__ == '__main__':
    app.run(debug=True)
