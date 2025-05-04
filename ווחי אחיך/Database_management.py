import pandas as pd
from typing import Optional, List, Dict, Tuple
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

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
                father_id: Optional[int] = None, father_in_law_id: Optional[int] = None) -> Person:
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
            father_id=father_id,
            father_in_law_id=father_in_law_id
        )
        session.add(person)
        session.commit()
        session.refresh(person)
        session.close()
        return person
    
    def find_person(self, title: Optional[str], first_name: str, last_name: str, 
                    father_name_hint: Optional[str] = None) -> Optional[Person]:
        
        session = self.Session()
        
        # Basic query
        query = session.query(Person).filter(
            Person.first_name == first_name.strip(),
            Person.last_name == last_name.strip()
        )
        
        # Add title filter if provided
        if title:
            query = query.filter(Person.title == title.strip())
        
        candidates = query.all()
        
        # If multiple candidates and father hint is provided
        if len(candidates) > 1 and father_name_hint:
            filtered = []
            for candidate in candidates:
                if candidate.father and candidate.father.first_name.startswith(father_name_hint):
                    filtered.append(candidate)
            
            if filtered:
                session.close()
                return filtered[0]
        
        session.close()
        return candidates[0] if candidates else None
    
    def process_father_and_father_in_law(self):
        session = self.Session()
        people = session.query(Person).all()
        
        # מעבדים את כל האנשים בשתי סבבים
        for _ in range(2):  # שתי פעמים לוודא שכל הקשרים מתעדכנים
            for person in people:
                # עיבוד אב
                if hasattr(person, '_father_raw') and person._father_raw and pd.notna(person._father_raw):
                    self._process_relative(session, person, person._father_raw, 'father')
                
                # עיבוד חמיו
                if hasattr(person, '_father_in_law_raw') and person._father_in_law_raw and pd.notna(person._father_in_law_raw):
                    self._process_relative(session, person, person._father_in_law_raw, 'father_in_law')
        
        session.commit()  # מבצעים commit רק בסוף
        session.close()
    
    def _process_relative(self, session, person: Person, relative_info: str, 
                        relation_type: str, relative_id: Optional[int] = None) -> bool:
        """
        עיבוד יחס משפחתי עם ID ישיר
        """
        if relative_id is not None:
            setattr(person, f'{relation_type}_id', relative_id)
            session.add(person)
            return True
        
        if not relative_info or pd.isna(relative_info):
            return False
            
        relative_info = str(relative_info).strip()
        if not relative_info:
            return False
                
        # חיפוש הקשר לפי המידע המסופק
        relative = self.find_person(None, relative_info, person.last_name)
                
        if relative:
            setattr(person, f'{relation_type}_id', relative.id)
            session.add(person)
            return True
                        
        return False
    
    def report_not_found(self):
        if not self.not_found_records:
            print("All relatives were found successfully!")
            return
        
        print(f"\nCould not find {len(self.not_found_records)} relatives:")
        for record in self.not_found_records:
            print(f"Person: {record['person_name']} (ID: {record['person_id']})")
            print(f"Relation: {record['relation_type']}, Relative Info: {record['relative_info']}")
            print("---")

def load_excel_data(file_path: str) -> pd.DataFrame:
    # Load the Excel file
    df = pd.read_excel(file_path)
    
    # Clean column names and data
    df.columns = [col.strip() for col in df.columns]
    
    # Convert all values to strings and strip whitespace
    df = df.applymap(lambda x: str(x).strip() if isinstance(x, str) else x)
    
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
                first_name=row.get('שם פרטי'),
                last_name=row.get('שם משפחה'),
                title=row.get('תואר לפני'),
                street=row.get('רחוב'),
                street_number=row.get('מס רחוב'),
                city=row.get('ישוב'),
                country=row.get('מדינה'),
                phone=row.get('טלפון'),
                mobile=row.get('טלפון נייד')
            )
        except ValueError as e:
            print(f"שגיאה בהוספת אדם: {e}")
    
    db.process_father_and_father_in_law()
    return db

def main():
    # Example usage - replace with your actual file path
    file_path = "db.xlsx"
    
    # You can use SQLite (default) or any other database supported by SQLAlchemy
    # For PostgreSQL: 'postgresql://user:password@localhost/dbname'
    # For MySQL: 'mysql://user:password@localhost/dbname'
    db_url = 'sqlite:///db.db'
    
    db = process_data(file_path, db_url)
    
    # Report on not found relatives
    db.report_not_found()
    
    print("\nDatabase created successfully!")

if __name__ == "__main__":
    main()