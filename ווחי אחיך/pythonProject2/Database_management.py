import pandas as pd
from typing import Optional, List, Dict, Tuple
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, aliased
import re  # לצורך זיהוי שם האב עם regex
import random

# שימוש בסינטקס החדש של SQLAlchemy 2.0
Base = declarative_base()


class Person(Base):
    __tablename__ = 'people'

    id = Column(Integer, primary_key=True)
    title = Column(String(50))
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    street = Column(String(100))
    street_number = Column(String(20))
    city = Column(String(100))
    country = Column(String(100))
    phone = Column(String(20))
    mobile = Column(String(20))
    father_raw = Column(Text)  # הוספת עמודה לשמירת שם האב הגולמי
    father_in_law_raw = Column(Text)  # הוספת עמודה לשמירת שם החם הגולמי

    father_id = Column(Integer, ForeignKey('people.id'))
    father_in_law_id = Column(Integer, ForeignKey('people.id'))

    father = relationship(
        "Person",
        foreign_keys=[father_id],
        remote_side=[id],
        post_update=True
    )
    father_in_law = relationship(
        "Person",
        foreign_keys=[father_in_law_id],
        remote_side=[id],
        post_update=True
    )

    def __repr__(self):
        return f"<Person(id={self.id}, name='{self.full_name()}')>"

    def full_name(self) -> str:
        return f"{self.title} {self.first_name} {self.last_name}"


class FamilyDatabase:
    def __init__(self, db_url: str = 'sqlite:///Database.db'):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.not_found_records = []

    def add_person(self, first_name: str, last_name: str, title: Optional[str] = None,
                   street: Optional[str] = None, street_number: Optional[str] = None,
                   city: Optional[str] = None, country: Optional[str] = None,
                   phone: Optional[str] = None, mobile: Optional[str] = None,
                   father_raw: Optional[str] = None, father_in_law_raw: Optional[str] = None) -> Person:
        session = self.Session()
        person = Person(
            title=title,
            first_name=first_name,
            last_name=last_name,
            street=street,
            street_number=street_number,
            city=city,
            country=country,
            phone=phone,
            mobile=mobile,
            father_raw=father_raw,
            father_in_law_raw=father_in_law_raw
        )

        session.add(person)
        session.commit()
        session.refresh(person)
        session.close()
        return person

    def find_person(self, first_name: str, last_name: str, father_initials: Optional[str] = None) -> List[Person]:
        session = self.Session()
        query = session.query(Person).filter(
            Person.first_name == first_name.strip(),
            Person.last_name == last_name.strip()
        )

        if father_initials:
            father_alias = aliased(Person)
            query = query.join(
                father_alias,
                Person.father_id == father_alias.id
            ).filter(
                father_alias.first_name.startswith(father_initials[0])
            )

        people = query.all()
        session.close()
        print(people, first_name, last_name, father_initials)
        return people

    def _process_complex_name(self, name_str: str, last_name: Optional[str] = None) -> Optional[Person]:
        name_str = str(name_str).strip()
        words = name_str.split()

        if len(words) < 2:
            return None

        # הסר תואר (מילה ראשונה)
        words = words[1:]

        # אם שם משפחה ניתן – אל תחלץ אותו מהמחרוזת
        if last_name:
            first_name_parts = words
        else:
            last_name = words[-1]
            first_name_parts = words[:-1]

        # חפש קידומת של שם האב
        father_initials = None
        for i, word in enumerate(first_name_parts):
            match = re.match(r'בר[\"\'”״]?([א-ת]{1,3})', word)
            if match:
                father_initials = match.group(1)
                first_name_parts.pop(i)
                break

        first_name = ' '.join(first_name_parts).strip()
        print(first_name,last_name, father_initials)
        # חיפוש דרך הפונקציה find_person
        people = self.find_person(first_name, last_name, father_initials)

        # בדיוק אחד = הצלחה, אחרת None
        if len(people) == 1:
            return people[0]
        return None

    def process_father_and_father_in_law(self):
        session = self.Session()
        people = session.query(Person).all()
        random.shuffle(people)  # ערבוב אקראי של הרשימה

        for person in people:
            # עיבוד אב
            if person.father_id is None or str(person.father_raw).strip() == "":
                father_name = str(person.father_raw).strip()
                # מטפל בשמות מורכבים
                father = self._process_complex_name(father_name, person.last_name)

                if father:
                    person.father_id = father.id
                else:
                    self.not_found_records.append({
                        'person_id': person.id,
                        'person_name': person.full_name(),
                        'relation_type': 'father',
                        'relative_info': father_name
                    })

            # עיבוד חמיו
            if person.father_in_law_id is None or str(person.father_raw).strip() == "":
                father_in_law_name = str(person.father_in_law_raw).strip()
                # מטפל בשמות מורכבים
                father_in_law  = self._process_complex_name(father_in_law_name)

                if father_in_law:
                    person.father_in_law_id = father_in_law.id
                else:
                    self.not_found_records.append({
                        'person_id': person.id,
                        'person_name': person.full_name(),
                        'relation_type': 'father_in_law',
                        'relative_info': father_in_law_name
                    })

        session.commit()
        session.close()


    def report_not_found(self):
        if not self.not_found_records:
            print("All relatives were found successfully!")
            return

        print(f"\nCould not find {len(self.not_found_records)} relatives:")
        for record in self.not_found_records:
            print(f"Person: {record['person_name']} (ID: {record['person_id']})")
            print(f"Relation: {record['relation_type']}, Relative Info: {record['relative_info']}")
            print("---")

    def check_family_relations(self) -> Dict[str, int]:
        """
        בודק את מצב הקשרים המשפחתיים במאגר הנתונים
        מחזיר מילון עם מספר האנשים שיש להם/אין להם אב וחם מוגדרים
        """
        session = self.Session()

        total_people = session.query(Person).count()
        with_father = session.query(Person).filter(Person.father_id.isnot(None)).count()
        with_father_in_law = session.query(Person).filter(Person.father_in_law_id.isnot(None)).count()

        session.close()

        report = {
            'total_people': total_people,
            'with_father': with_father,
            'without_father': total_people - with_father,
            'with_father_in_law': with_father_in_law,
            'without_father_in_law': total_people - with_father_in_law,
            'percentage_with_father': round((with_father / total_people) * 100, 2) if total_people > 0 else 0,
            'percentage_with_father_in_law': round((with_father_in_law / total_people) * 100,
                                                   2) if total_people > 0 else 0
        }

        print("\nFamily Relations Report:")
        print("=======================")
        print(f"Total people in database: {report['total_people']}")
        print(f"\nFather relationships:")
        print(f" - With father defined: {report['with_father']} ({report['percentage_with_father']}%)")
        print(f" - Without father defined: {report['without_father']}")
        print(f"\nFather-in-law relationships:")
        print(
            f" - With father-in-law defined: {report['with_father_in_law']} ({report['percentage_with_father_in_law']}%)")
        print(f" - Without father-in-law defined: {report['without_father_in_law']}")

        return report


def load_excel_data(file_path: str) -> pd.DataFrame:
    # Load the Excel file
    df = pd.read_excel(file_path, engine='openpyxl')

    # Clean column names and data
    df.columns = [col.strip() for col in df.columns]

    # Convert all values to strings and strip whitespace
    df = df.map(lambda x: str(x).strip() if isinstance(x, str) else x)

    # Replace empty strings with None
    df = df.replace(['', 'nan', 'None'], None)

    return df


def process_data(file_path: str, db_url: str = 'sqlite:///db.db') -> FamilyDatabase:
    df = load_excel_data(file_path)
    db = FamilyDatabase(db_url)

    # סינון שורות חסרות שם פרטי או משפחה
    df = df.dropna(subset=['שם פרטי', 'שם משפחה'])

    for _, row in df.iterrows():
        try:
            person = db.add_person(
                first_name=re.sub(r"\s*\(.*?\)", "", row.get('שם פרטי')),
                last_name=row.get('שם משפחה'),
                title=row.get('תואר לפני'),
                street=row.get('רחוב'),
                street_number=row.get('מס רחוב'),
                city=row.get('ישוב'),
                country=row.get('מדינה'),
                phone=row.get('טלפון'),
                mobile=row.get('טלפון נייד'),
                father_raw=row.get('שם האב'),
                father_in_law_raw=row.get('חתן')
            )
        except Exception as e:
            print(f"שגיאה בהוספת אדם: {e}")

    for _ in range(5):
        db.process_father_and_father_in_law()
    return db


def main():
    # Example usage - replace with your actual file path
    file_path = "db.xlsx"
    db_url = 'sqlite:///db.db'

    try:
        db = process_data(file_path, db_url)

        # Report on not found relatives
        db.report_not_found()

        # Check family relations status
        db.check_family_relations()

        print("\nDatabase created successfully!")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'db' in locals():
            # Ensure session is closed
            db.engine.dispose()


if __name__ == "__main__":
    main()
