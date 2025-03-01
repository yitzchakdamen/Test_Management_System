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
