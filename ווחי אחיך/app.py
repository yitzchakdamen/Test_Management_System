from flask import Flask, request, jsonify, render_template
from typing import List, Dict, Any
from sqlalchemy import or_, and_
from sqlalchemy.orm import joinedload
import json
import os

app = Flask(__name__, template_folder='templates')  # מניח שקובצי ה-HTML נמצאים בתיקייה templates

# נשתמש במחלקות שכבר הגדרת מהקוד הקודם
from Database_management import FamilyDatabase, Person, Base

# נאתחל את מסד הנתונים
db = FamilyDatabase('sqlite:///db.db')

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')  # מניח שיש לך קובץ בשם index.html בתיקיית templates

@app.route('/search', methods=['POST'])
def search_people():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No search criteria provided"}), 400
        
        session = db.Session()
        query = session.query(Person)
        
        # חיפוש לפי שם פרטי (אם מולא)
        if data.get('first_name'):
            query = query.filter(Person.first_name.ilike(f"%{data['first_name']}%"))
        
        # חיפוש לפי שם משפחה (אם מולא)
        if data.get('last_name'):
            query = query.filter(Person.last_name.ilike(f"%{data['last_name']}%"))
        
        # חיפוש לפי עיר (אם מולא)
        if data.get('city'):
            query = query.filter(Person.city.ilike(f"%{data['city']}%"))
        
        # חיפוש לפי טלפון (אם מולא)
        if data.get('phone'):
            query = query.filter(or_(
                Person.phone.ilike(f"%{data['phone']}%"),
                Person.mobile.ilike(f"%{data['phone']}%")
            ))
        
        # הגבלת תוצאות ל-10 והחזרת התוצאות
        results = query.limit(10).all()
        session.close()
        
        people_list = [{
            "id": p.id,
            "title": p.title,
            "first_name": p.first_name,
            "last_name": p.last_name,
            "city": p.city,
            "phone": p.phone,
            "mobile": p.mobile
        } for p in results]
        
        return jsonify(people_list)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/family/<int:person_id>', methods=['GET'])
def get_family(person_id):
    """מחזיר את כל המידע המשפחתי עבור אדם מסוים"""
    try:
        session = db.Session()
        
        # מצא את האדם הראשי
        main_person = session.query(Person).get(person_id)
        if not main_person:
            return jsonify({"error": "Person not found"}), 404
        
        # חפש ילדים - אלה שרשום אצלם האב הוא האדם הנוכחי
        children = session.query(Person).filter(Person.father_id == person_id).all()
        
        # חפש אחים - אלה שיש להם אותו אב כמו האדם הנוכחי
        siblings = []
        if main_person.father_id:
            siblings = session.query(Person).filter(
                Person.father_id == main_person.father_id,
                Person.id != person_id
            ).all()
        
        # חפש גיסים - אלה שהחותן שלהם הוא החותן של האדם הנוכחי
        brothers_in_law = []
        if main_person.father_in_law_id:
            brothers_in_law = session.query(Person).filter(
                Person.father_in_law_id == main_person.father_in_law_id,
                Person.id != person_id
            ).all()
        
        # איסוף כל הנתונים
        result = {
            "main_person": {
                "id": main_person.id,
                "title": main_person.title,
                "first_name": main_person.first_name,
                "last_name": main_person.last_name,
                "phone": main_person.phone,
                "mobile": main_person.mobile,
                "address": f"{main_person.street} {main_person.street_number}, {main_person.city}"
            },
            "father": get_person_info(session, main_person.father_id),
            "father_in_law": get_person_info(session, main_person.father_in_law_id),
            "children": [get_person_info(session, child.id) for child in children],
            "siblings": [get_person_info(session, sibling.id) for sibling in siblings],
            "brothers_in_law": [get_person_info(session, bro.id) for bro in brothers_in_law]
        }
        session.close()
        
        print(f"Found family for person ID {person_id}: {json.dumps(result, indent=2, ensure_ascii=False)}")
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_person_info(session, person_id):
    """פונקציית עזר להחזרת מידע על אדם"""
    if not person_id:
        return None
    
    person = session.query(Person).get(person_id)
    if not person:
        return None
    
    return {
        "id": person.id,
        "title": person.title,
        "first_name": person.first_name,
        "last_name": person.last_name,
        "phone": person.phone,
        "mobile": person.mobile,
        "address": f"{person.street} {person.street_number}, {person.city}" if person.street else None
    }

if __name__ == '__main__':
    # וודא שתיקיית ה-templates קיימת
    if not os.path.exists('templates'):
        os.makedirs('templates')
        print("Created 'templates' directory - please add your HTML files there")
    
    app.run(debug=True)