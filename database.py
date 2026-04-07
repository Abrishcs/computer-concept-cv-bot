import sqlite3
import json
from datetime import datetime

class Database:
    def __init__(self, db_path='cv_builder.db'):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        with self.get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    full_name TEXT,
                    phone TEXT,
                    email TEXT,
                    city TEXT,
                    social TEXT,
                    university TEXT,
                    degree TEXT,
                    edu_year TEXT,
                    gpa TEXT,
                    education TEXT,
                    profile TEXT,
                    skills TEXT,
                    soft_skills TEXT,
                    projects TEXT,
                    experience TEXT,
                    certifications TEXT,
                    languages TEXT,
                    photo_file_id TEXT,
                    status TEXT DEFAULT 'started',
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
            ''')
            conn.commit()

            # Add new columns to existing tables (safe migration)
            new_columns = [
                ('social', 'TEXT'),
                ('university', 'TEXT'),
                ('degree', 'TEXT'),
                ('edu_year', 'TEXT'),
                ('gpa', 'TEXT'),
                ('payment_status', 'TEXT DEFAULT "unpaid"'),
            ]
            for col_name, col_type in new_columns:
                try:
                    conn.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
                    conn.commit()
                except sqlite3.OperationalError:
                    # Column already exists
                    pass

    def update_user(self, user_id, **kwargs):
        kwargs['updated_at'] = datetime.now().isoformat()
        columns = ', '.join(f"{k} = ?" for k in kwargs.keys())
        values = list(kwargs.values())
        values.append(user_id)

        with self.get_connection() as conn:
            # Check if user exists
            cursor = conn.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
            if not cursor.fetchone():
                # Insert initial record
                initial_data = {'user_id': user_id, 'created_at': kwargs['updated_at']}
                cols = ', '.join(initial_data.keys())
                placeholders = ', '.join(['?'] * len(initial_data))
                conn.execute(f"INSERT INTO users ({cols}) VALUES ({placeholders})", list(initial_data.values()))

            # Update record
            conn.execute(f"UPDATE users SET {columns} WHERE user_id = ?", values)
            conn.commit()

    def get_user(self, user_id):
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def save_cv_data(self, user_id, data):
        # Flatten dictionary for SQLite
        update_fields = {}
        # List of valid columns in the users table to avoid trying to save non-existent columns
        valid_columns = {
            'username', 'full_name', 'phone', 'email', 'city', 'social',
            'university', 'degree', 'edu_year', 'gpa', 'education',
            'profile', 'skills', 'soft_skills', 'projects', 'experience',
            'certifications', 'languages', 'photo_file_id', 'status', 'payment_status'
        }

        for key, value in data.items():
            if key not in valid_columns:
                continue

            if value is None:
                update_fields[key] = None
            elif isinstance(value, (dict, list)):
                update_fields[key] = json.dumps(value)
            else:
                # Ensure it's a string for TEXT columns
                update_fields[key] = str(value)

        if update_fields:
            self.update_user(user_id, **update_fields)

    def get_stats(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE payment_status = 'paid'")
            total_paid = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE payment_status = 'pending'")
            total_pending = cursor.fetchone()[0]
            
            return {
                "total_users": total_users,
                "total_paid": total_paid,
                "total_pending": total_pending,
                "revenue": total_paid * 20
            }

    def get_all_user_ids(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users")
            return [row[0] for row in cursor.fetchall()]
