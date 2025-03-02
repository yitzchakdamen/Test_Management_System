import hashlib
from database.database import Database


class Authentication:
    def __init__(self, db):
        self.db = db

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def register_user(self, username, password, user_type="student"):
        cursor = self.db.conn.cursor()
        hashed_password = self.hash_password(password)
        try:
            cursor.execute('''
                INSERT INTO users (username, password, user_type)
                VALUES (?, ?, ?)
            ''', (username, hashed_password, user_type))
            self.db.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def login(self, username, password):
        cursor = self.db.conn.cursor()
        hashed_password = self.hash_password(password)
        cursor.execute('''
            SELECT * FROM users 
            WHERE username = ? AND password = ?
        ''', (username, hashed_password))
        return cursor.fetchone()
