import sqlite3
import os
import uuid
import bcrypt
from datetime import datetime
from src.config import Config

# Optional Postgres support for direct Postgres URL (no Supabase HTTP key required)
try:
    import psycopg2
    import psycopg2.extras
    _PSYCOPG_AVAILABLE = True
except Exception:
    _PSYCOPG_AVAILABLE = False

# Lazy import: only load supabase if actually configured
try:
    from supabase import create_client, Client
    _SUPABASE_AVAILABLE = True
except ImportError:
    _SUPABASE_AVAILABLE = False

# Interface definition and factory for DB operations
class Database:
    _instance = None

    @classmethod
    def get_client(cls):
        if cls._instance is None:
            if Config.IS_SUPABASE_CONFIGURED:
                # If user provided a direct Postgres URL, use PostgresAdapter
                if getattr(Config, "POSTGRES_DIRECT", False):
                    try:
                        cls._instance = PostgresAdapter(Config.SUPABASE_URL)
                    except Exception as e:
                        print(f"Failed to connect to Postgres: {e}. Falling back to SQLite.")
                        cls._instance = SQLiteAdapter(Config.SQLITE_DB_NAME)
                else:
                    try:
                        cls._instance = SupabaseAdapter(Config.SUPABASE_URL, Config.SUPABASE_KEY)
                    except Exception as e:
                        print(f"Failed to connect to Supabase: {e}. Falling back to SQLite.")
                        cls._instance = SQLiteAdapter(Config.SQLITE_DB_NAME)
            else:
                cls._instance = SQLiteAdapter(Config.SQLITE_DB_NAME)
        return cls._instance

class SupabaseAdapter:
    def __init__(self, url: str, key: str):
        if not _SUPABASE_AVAILABLE:
            raise ImportError("supabase package is not installed. Run: pip install supabase")
        self.client: Client = create_client(url, key)
        self.mode = "Supabase"

    def init_db(self):
        # Database schema is pre-configured in Supabase console using database/schema.sql
        pass

    # --- ADMINS ---
    def get_admin_by_id(self, admin_id):
        res = self.client.table("admins").select("*").eq("id", admin_id).execute()
        return res.data[0] if res.data else None

    def get_admin_by_email(self, email):
        res = self.client.table("admins").select("*").eq("email", email).execute()
        return res.data[0] if res.data else None

    def create_admin(self, admin_id, email, name):
        data = {"id": str(admin_id), "email": email, "name": name}
        res = self.client.table("admins").insert(data).execute()
        return res.data[0] if res.data else None

    # --- STUDENTS ---
    def get_student_by_id(self, student_id):
        res = self.client.table("students").select("*").eq("id", student_id).execute()
        return res.data[0] if res.data else None

    def get_student_by_email(self, email):
        res = self.client.table("students").select("*").eq("email", email).execute()
        return res.data[0] if res.data else None

    def get_student_by_roll(self, roll_number):
        res = self.client.table("students").select("*").eq("roll_number", roll_number).execute()
        return res.data[0] if res.data else None

    def create_student(self, student_id, email, name, roll_number, phone):
        data = {
            "id": str(student_id),
            "email": email,
            "name": name,
            "roll_number": roll_number,
            "phone": phone
        }
        res = self.client.table("students").insert(data).execute()
        return res.data[0] if res.data else None

    def get_all_students(self):
        res = self.client.table("students").select("*").order("created_at").execute()
        return res.data

    def update_student(self, student_id, name, roll_number, phone):
        data = {"name": name, "roll_number": roll_number, "phone": phone}
        res = self.client.table("students").update(data).eq("id", student_id).execute()
        return res.data[0] if res.data else None

    def delete_student(self, student_id):
        res = self.client.table("students").delete().eq("id", student_id).execute()
        return len(res.data) > 0

    # --- QUESTION BANK ---
    def get_all_questions(self):
        res = self.client.table("question_bank").select("*").order("id").execute()
        return res.data

    def get_questions_by_topic(self, topic):
        res = self.client.table("question_bank").select("*").eq("topic", topic).execute()
        return res.data

    def add_question(self, topic, question_text, question_type, option_a, option_b, option_c, option_d, correct_option, difficulty):
        data = {
            "topic": topic,
            "question_text": question_text,
            "question_type": question_type,
            "option_a": option_a,
            "option_b": option_b,
            "option_c": option_c,
            "option_d": option_d,
            "correct_option": correct_option,
            "difficulty": difficulty
        }
        res = self.client.table("question_bank").insert(data).execute()
        return res.data[0] if res.data else None

    def update_question(self, question_id, topic, question_text, question_type, option_a, option_b, option_c, option_d, correct_option, difficulty):
        data = {
            "topic": topic,
            "question_text": question_text,
            "question_type": question_type,
            "option_a": option_a,
            "option_b": option_b,
            "option_c": option_c,
            "option_d": option_d,
            "correct_option": correct_option,
            "difficulty": difficulty
        }
        res = self.client.table("question_bank").update(data).eq("id", question_id).execute()
        return res.data[0] if res.data else None

    def delete_question(self, question_id):
        res = self.client.table("question_bank").delete().eq("id", question_id).execute()
        return len(res.data) > 0

    def bulk_upload_questions(self, df):
        # Expected df columns: ['topic', 'question_text', 'question_type', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_option', 'difficulty']
        records = df.to_dict(orient="records")
        res = self.client.table("question_bank").insert(records).execute()
        return len(res.data)

    # --- EXAMS ---
    def get_all_exams(self):
        res = self.client.table("exams").select("*").order("created_at").execute()
        return res.data

    def get_active_exams(self):
        res = self.client.table("exams").select("*").eq("is_active", True).order("created_at").execute()
        return res.data

    def create_exam(self, title, description, duration_minutes, total_questions, passing_percentage, is_active, question_ids):
        data = {
            "title": title,
            "description": description,
            "duration_minutes": int(duration_minutes),
            "total_questions": int(total_questions),
            "passing_percentage": float(passing_percentage),
            "is_active": bool(is_active)
        }
        res = self.client.table("exams").insert(data).execute()
        if not res.data:
            return None
        exam = res.data[0]
        
        # Insert exam questions mapping
        mapping = [{"exam_id": exam["id"], "question_id": q_id} for q_id in question_ids]
        if mapping:
            self.client.table("exam_questions").insert(mapping).execute()
            
        return exam

    def update_exam(self, exam_id, title, description, duration_minutes, total_questions, passing_percentage, is_active, question_ids):
        data = {
            "title": title,
            "description": description,
            "duration_minutes": int(duration_minutes),
            "total_questions": int(total_questions),
            "passing_percentage": float(passing_percentage),
            "is_active": bool(is_active)
        }
        res = self.client.table("exams").update(data).eq("id", exam_id).execute()
        if not res.data:
            return None
        
        # Delete old mappings and insert new
        self.client.table("exam_questions").delete().eq("exam_id", exam_id).execute()
        mapping = [{"exam_id": exam_id, "question_id": q_id} for q_id in question_ids]
        if mapping:
            self.client.table("exam_questions").insert(mapping).execute()
            
        return res.data[0]

    def delete_exam(self, exam_id):
        res = self.client.table("exams").delete().eq("id", exam_id).execute()
        return len(res.data) > 0

    def get_exam_questions(self, exam_id):
        # Fetch question details linked to the exam
        res = self.client.table("exam_questions").select("question_id").eq("exam_id", exam_id).execute()
        if not res.data:
            return []
        q_ids = [item["question_id"] for item in res.data]
        res_q = self.client.table("question_bank").select("*").in_("id", q_ids).execute()
        return res_q.data

    # --- RESULTS & RESPONSES ---
    def create_result(self, student_id, exam_id, score, total_questions, percentage, grade, passed, started_at, submitted_at):
        data = {
            "student_id": str(student_id),
            "exam_id": int(exam_id),
            "score": int(score),
            "total_questions": int(total_questions),
            "percentage": float(percentage),
            "grade": grade,
            "passed": bool(passed),
            "started_at": started_at.isoformat() if isinstance(started_at, datetime) else started_at,
            "submitted_at": submitted_at.isoformat() if isinstance(submitted_at, datetime) else submitted_at
        }
        res = self.client.table("results").insert(data).execute()
        return res.data[0] if res.data else None

    def save_responses(self, result_id, responses_list):
        # responses_list format: [{"question_id": int, "selected_option": str, "is_correct": bool}]
        mapping = []
        for r in responses_list:
            mapping.append({
                "result_id": result_id,
                "question_id": r["question_id"],
                "selected_option": r["selected_option"],
                "is_correct": r["is_correct"]
            })
        if mapping:
            res = self.client.table("responses").insert(mapping).execute()
            return len(res.data)
        return 0

    def get_student_results(self, student_id):
        # Fetch results with exam details
        res = self.client.table("results").select("*, exams(title)").eq("student_id", student_id).order("submitted_at", desc=True).execute()
        return res.data

    def get_all_results(self):
        res = self.client.table("results").select("*, exams(title), students(name, roll_number)").order("submitted_at", desc=True).execute()
        return res.data

    def get_result_by_id(self, result_id):
        res = self.client.table("results").select("*, exams(*), students(*)").eq("id", result_id).execute()
        return res.data[0] if res.data else None

    def get_result_responses(self, result_id):
        res = self.client.table("responses").select("*, question_bank(*)").eq("result_id", result_id).execute()
        return res.data

    # --- TYPING RESULTS ---
    def create_typing_result(self, result_id, wpm, accuracy, passage_text, typed_text, passed):
        data = {
            "result_id": int(result_id),
            "wpm": int(wpm),
            "accuracy": float(accuracy),
            "passage_text": passage_text,
            "typed_text": typed_text,
            "passed": bool(passed)
        }
        res = self.client.table("typing_results").insert(data).execute()
        return res.data[0] if res.data else None

    def get_typing_result_by_result_id(self, result_id):
        res = self.client.table("typing_results").select("*").eq("result_id", result_id).execute()
        return res.data[0] if res.data else None

    # --- CERTIFICATES ---
    def get_certificate_by_result_id(self, result_id):
        res = self.client.table("certificates").select("*").eq("result_id", result_id).execute()
        return res.data[0] if res.data else None

    def create_certificate(self, certificate_id, student_id, result_id):
        data = {
            "certificate_id": certificate_id,
            "student_id": str(student_id),
            "result_id": int(result_id)
        }
        res = self.client.table("certificates").insert(data).execute()
        return res.data[0] if res.data else None

    def get_certificate_by_id(self, certificate_id):
        res = self.client.table("certificates").select("*, students(*), results(*, exams(*))").eq("certificate_id", certificate_id).execute()
        return res.data[0] if res.data else None



class PostgresAdapter:
    def __init__(self, dsn: str):
        if not _PSYCOPG_AVAILABLE:
            raise ImportError("psycopg2 is not installed. Run: pip install psycopg2-binary")
        self.dsn = dsn
        self.mode = "Postgres"
        # Ensure schema is applied and local_auth exists
        self.init_db()

    def _get_connection(self):
        if not hasattr(self, 'pool'):
            from psycopg2.pool import ThreadedConnectionPool
            # Initialize pool with min 1, max 20 connections
            self.pool = ThreadedConnectionPool(1, 20, self.dsn)

        conn = self.pool.getconn()
        
        class ConnProxy:
            def __init__(self, c, p):
                self._conn = c
                self._pool = p
            def cursor(self, *args, **kwargs):
                return self._conn.cursor(*args, **kwargs)
            def commit(self):
                self._conn.commit()
            def rollback(self):
                self._conn.rollback()
            def close(self):
                self._pool.putconn(self._conn)
                
        return ConnProxy(conn, self.pool)

    def init_db(self):
        conn = None
        try:
            conn = self._get_connection()
            cur = conn.cursor()

            # Create local_auth table for storing local credentials (if not using Supabase Auth)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS local_auth (
                id VARCHAR(100) PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role VARCHAR(50) NOT NULL
            )""")
            conn.commit()

            # Apply schema.sql (assume it's compatible with Postgres)
            schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "schema.sql")
            if os.path.exists(schema_path):
                with open(schema_path, "r") as f:
                    schema_sql = f.read()
                # Execute statements individually
                for statement in schema_sql.split(";"):
                    stmt = statement.strip()
                    if not stmt:
                        continue
                    try:
                        cur.execute(stmt)
                        conn.commit()
                    except Exception:
                        conn.rollback()

            # Seed default admin user in local_auth and admins tables if not exists
            admin_id = str(uuid.uuid4())
            admin_email = "admin@bcc.com"
            admin_name = "System Admin"
            admin_pass_hash = bcrypt.hashpw("admin123".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

            # Insert admin into admins and local_auth if not already present
            try:
                cur.execute("SELECT id FROM admins WHERE email = %s", (admin_email,))
                if not cur.fetchone():
                    cur.execute("INSERT INTO admins (id, email, name) VALUES (%s, %s, %s)", (admin_id, admin_email, admin_name))
                cur.execute("SELECT id FROM local_auth WHERE email = %s", (admin_email,))
                if not cur.fetchone():
                    cur.execute("INSERT INTO local_auth (id, email, password_hash, role) VALUES (%s, %s, %s, %s)", (admin_id, admin_email, admin_pass_hash, 'admin'))
            except Exception:
                pass

            conn.commit()
        finally:
            if conn:
                conn.close()

    def _to_dict(self, row):
        return dict(row) if row else None

    def _to_list(self, rows):
        return [dict(r) for r in rows]

    # --- ADMINS ---
    def get_admin_by_id(self, admin_id):
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM admins WHERE id = %s", (str(admin_id),))
        row = cur.fetchone()
        conn.close()
        return self._to_dict(row)

    def get_admin_by_email(self, email):
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM admins WHERE email = %s", (email,))
        row = cur.fetchone()
        conn.close()
        return self._to_dict(row)

    def create_admin(self, admin_id, email, name):
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("INSERT INTO admins (id, email, name) VALUES (%s, %s, %s)", (str(admin_id), email, name))
        conn.commit()
        cur.execute("SELECT * FROM admins WHERE id = %s", (str(admin_id),))
        row = cur.fetchone()
        conn.close()
        return self._to_dict(row)

    # --- STUDENTS ---
    def get_student_by_id(self, student_id):
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM students WHERE id = %s", (str(student_id),))
        row = cur.fetchone()
        conn.close()
        return self._to_dict(row)

    def get_student_by_email(self, email):
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM students WHERE email = %s", (email,))
        row = cur.fetchone()
        conn.close()
        return self._to_dict(row)

    def get_student_by_roll(self, roll_number):
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM students WHERE roll_number = %s", (roll_number,))
        row = cur.fetchone()
        conn.close()
        return self._to_dict(row)

    def create_student(self, student_id, email, name, roll_number, phone):
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("INSERT INTO students (id, email, name, roll_number, phone) VALUES (%s, %s, %s, %s, %s)",
                    (str(student_id), email, name, roll_number, phone))
        conn.commit()
        cur.execute("SELECT * FROM students WHERE id = %s", (str(student_id),))
        row = cur.fetchone()
        conn.close()
        return self._to_dict(row)

    def get_all_students(self):
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM students ORDER BY created_at")
        rows = cur.fetchall()
        conn.close()
        return self._to_list(rows)

    def update_student(self, student_id, name, roll_number, phone):
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("UPDATE students SET name = %s, roll_number = %s, phone = %s WHERE id = %s",
                    (name, roll_number, phone, str(student_id)))
        conn.commit()
        cur.execute("SELECT * FROM students WHERE id = %s", (str(student_id),))
        row = cur.fetchone()
        conn.close()
        return self._to_dict(row)

    def delete_student(self, student_id):
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM students WHERE id = %s", (str(student_id),))
        conn.commit()
        count = cur.rowcount
        conn.close()
        return count > 0

    # --- QUESTION BANK ---
    def get_all_questions(self):
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM question_bank ORDER BY id")
        rows = cur.fetchall()
        conn.close()
        return self._to_list(rows)

    def get_questions_by_topic(self, topic):
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM question_bank WHERE topic = %s", (topic,))
        rows = cur.fetchall()
        conn.close()
        return self._to_list(rows)

    def add_question(self, topic, question_text, question_type, option_a, option_b, option_c, option_d, correct_option, difficulty):
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("INSERT INTO question_bank (topic, question_text, question_type, option_a, option_b, option_c, option_d, correct_option, difficulty) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
                    (topic, question_text, question_type, option_a, option_b, option_c, option_d, correct_option, difficulty))
        inserted = cur.fetchone()
        conn.commit()
        cur.execute("SELECT * FROM question_bank WHERE id = %s", (inserted['id'],))
        row = cur.fetchone()
        conn.close()
        return self._to_dict(row)

    def update_question(self, question_id, topic, question_text, question_type, option_a, option_b, option_c, option_d, correct_option, difficulty):
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("UPDATE question_bank SET topic = %s, question_text = %s, question_type = %s, option_a = %s, option_b = %s, option_c = %s, option_d = %s, correct_option = %s, difficulty = %s WHERE id = %s",
                    (topic, question_text, question_type, option_a, option_b, option_c, option_d, correct_option, difficulty, question_id))
        conn.commit()
        cur.execute("SELECT * FROM question_bank WHERE id = %s", (question_id,))
        row = cur.fetchone()
        conn.close()
        return self._to_dict(row)

    def delete_question(self, question_id):
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM question_bank WHERE id = %s", (question_id,))
        conn.commit()
        count = cur.rowcount
        conn.close()
        return count > 0

    def bulk_upload_questions(self, df):
        conn = self._get_connection()
        cur = conn.cursor()
        count = 0
        for _, row in df.iterrows():
            cur.execute("INSERT INTO question_bank (topic, question_text, question_type, option_a, option_b, option_c, option_d, correct_option, difficulty) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (row['topic'], row['question_text'], row['question_type'], row.get('option_a'), row.get('option_b'), row.get('option_c'), row.get('option_d'), row['correct_option'], row['difficulty']))
            count += 1
        conn.commit()
        conn.close()
        return count

    # --- EXAMS ---
    def get_all_exams(self):
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM exams ORDER BY created_at")
        rows = cur.fetchall()
        conn.close()
        return self._to_list(rows)

    def get_active_exams(self):
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM exams WHERE is_active = TRUE ORDER BY created_at")
        rows = cur.fetchall()
        conn.close()
        return self._to_list(rows)

    def create_exam(self, title, description, duration_minutes, total_questions, passing_percentage, is_active, question_ids):
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("INSERT INTO exams (title, description, duration_minutes, total_questions, passing_percentage, is_active) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                    (title, description, int(duration_minutes), int(total_questions), float(passing_percentage), bool(is_active)))
        inserted = cur.fetchone()
        exam_id = inserted['id']
        for q_id in question_ids:
            cur.execute("INSERT INTO exam_questions (exam_id, question_id) VALUES (%s, %s)", (exam_id, q_id))
        conn.commit()
        cur.execute("SELECT * FROM exams WHERE id = %s", (exam_id,))
        row = cur.fetchone()
        conn.close()
        return self._to_dict(row)

    def update_exam(self, exam_id, title, description, duration_minutes, total_questions, passing_percentage, is_active, question_ids):
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("UPDATE exams SET title = %s, description = %s, duration_minutes = %s, total_questions = %s, passing_percentage = %s, is_active = %s WHERE id = %s",
                    (title, description, int(duration_minutes), int(total_questions), float(passing_percentage), bool(is_active), exam_id))
        cur.execute("DELETE FROM exam_questions WHERE exam_id = %s", (exam_id,))
        for q_id in question_ids:
            cur.execute("INSERT INTO exam_questions (exam_id, question_id) VALUES (%s, %s)", (exam_id, q_id))
        conn.commit()
        cur.execute("SELECT * FROM exams WHERE id = %s", (exam_id,))
        row = cur.fetchone()
        conn.close()
        return self._to_dict(row)

    def delete_exam(self, exam_id):
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM exams WHERE id = %s", (exam_id,))
        conn.commit()
        count = cur.rowcount
        conn.close()
        return count > 0

    def get_exam_questions(self, exam_id):
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT q.* FROM question_bank q JOIN exam_questions eq ON q.id = eq.question_id WHERE eq.exam_id = %s", (exam_id,))
        rows = cur.fetchall()
        conn.close()
        return self._to_list(rows)

    # --- RESULTS & RESPONSES ---
    def create_result(self, student_id, exam_id, score, total_questions, percentage, grade, passed, started_at, submitted_at):
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        started_str = started_at.isoformat() if isinstance(started_at, datetime) else str(started_at)
        submitted_str = submitted_at.isoformat() if isinstance(submitted_at, datetime) else str(submitted_at)
        cur.execute("INSERT INTO results (student_id, exam_id, score, total_questions, percentage, grade, passed, started_at, submitted_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
                    (str(student_id), int(exam_id), int(score), int(total_questions), float(percentage), grade, bool(passed), started_str, submitted_str))
        inserted = cur.fetchone()
        result_id = inserted['id']
        conn.commit()
        cur.execute("SELECT * FROM results WHERE id = %s", (result_id,))
        row = cur.fetchone()
        conn.close()
        return self._to_dict(row)

    def save_responses(self, result_id, responses_list):
        conn = self._get_connection()
        cur = conn.cursor()
        count = 0
        for r in responses_list:
            cur.execute("INSERT INTO responses (result_id, question_id, selected_option, is_correct) VALUES (%s, %s, %s, %s)",
                        (result_id, r["question_id"], r["selected_option"], True if r["is_correct"] else False))
            count += 1
        conn.commit()
        conn.close()
        return count

    def get_student_results(self, student_id):
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT r.*, e.title as exam_title FROM results r JOIN exams e ON r.exam_id = e.id WHERE r.student_id = %s ORDER BY r.submitted_at DESC", (str(student_id),))
        rows = cur.fetchall()
        conn.close()
        results = []
        for r in rows:
            d = dict(r)
            d["exams"] = {"title": d.get("exam_title")}
            results.append(d)
        return results

    def get_all_results(self):
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT r.*, e.title as exam_title, s.name as student_name, s.roll_number as student_roll FROM results r JOIN exams e ON r.exam_id = e.id JOIN students s ON r.student_id = s.id ORDER BY r.submitted_at DESC")
        rows = cur.fetchall()
        conn.close()
        results = []
        for r in rows:
            d = dict(r)
            d["exams"] = {"title": d.get("exam_title")}
            d["students"] = {"name": d.get("student_name"), "roll_number": d.get("student_roll")}
            results.append(d)
        return results

    def get_result_by_id(self, result_id):
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM results WHERE id = %s", (result_id,))
        row_res = cur.fetchone()
        if not row_res:
            conn.close()
            return None
        res_dict = dict(row_res)
        cur.execute("SELECT * FROM exams WHERE id = %s", (res_dict["exam_id"],))
        row_exam = cur.fetchone()
        res_dict["exams"] = dict(row_exam) if row_exam else None
        cur.execute("SELECT * FROM students WHERE id = %s", (res_dict["student_id"],))
        row_stud = cur.fetchone()
        res_dict["students"] = dict(row_stud) if row_stud else None
        conn.close()
        return res_dict

    def get_result_responses(self, result_id):
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT resp.*, q.topic, q.question_text, q.question_type, q.option_a, q.option_b, q.option_c, q.option_d, q.correct_option, q.difficulty FROM responses resp JOIN question_bank q ON resp.question_id = q.id WHERE resp.result_id = %s", (result_id,))
        rows = cur.fetchall()
        conn.close()
        responses = []
        for r in rows:
            d = dict(r)
            d["question_bank"] = {
                "id": d["question_id"],
                "topic": d["topic"],
                "question_text": d["question_text"],
                "question_type": d["question_type"],
                "option_a": d["option_a"],
                "option_b": d["option_b"],
                "option_c": d["option_c"],
                "option_d": d["option_d"],
                "correct_option": d["correct_option"],
                "difficulty": d["difficulty"]
            }
            responses.append(d)
        return responses

    # --- TYPING RESULTS ---
    def create_typing_result(self, result_id, wpm, accuracy, passage_text, typed_text, passed):
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            INSERT INTO typing_results (result_id, wpm, accuracy, passage_text, typed_text, passed)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING *
        """, (result_id, wpm, accuracy, passage_text, typed_text, passed))
        res = cur.fetchone()
        conn.commit()
        conn.close()
        return self._to_dict(res)

    def get_typing_result_by_result_id(self, result_id):
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM typing_results WHERE result_id = %s", (result_id,))
        row = cur.fetchone()
        conn.close()
        return self._to_dict(row)

    # --- CERTIFICATES ---
    def get_certificate_by_result_id(self, result_id):
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM certificates WHERE result_id = %s", (result_id,))
        row = cur.fetchone()
        conn.close()
        return self._to_dict(row)

    def create_certificate(self, certificate_id, student_id, result_id):
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("INSERT INTO certificates (certificate_id, student_id, result_id) VALUES (%s, %s, %s)", (certificate_id, str(student_id), result_id))
        conn.commit()
        cur.execute("SELECT * FROM certificates WHERE certificate_id = %s", (certificate_id,))
        row = cur.fetchone()
        conn.close()
        return self._to_dict(row)

    def get_certificate_by_id(self, certificate_id):
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM certificates WHERE certificate_id = %s", (certificate_id,))
        row_cert = cur.fetchone()
        if not row_cert:
            conn.close()
            return None
        cert_dict = dict(row_cert)
        cur.execute("SELECT * FROM students WHERE id = %s", (cert_dict["student_id"],))
        row_stud = cur.fetchone()
        cert_dict["students"] = dict(row_stud) if row_stud else None
        cur.execute("SELECT * FROM results WHERE id = %s", (cert_dict["result_id"],))
        row_res = cur.fetchone()
        if row_res:
            res_dict = dict(row_res)
            cur.execute("SELECT * FROM exams WHERE id = %s", (res_dict["exam_id"],))
            row_exam = cur.fetchone()
            res_dict["exams"] = dict(row_exam) if row_exam else None
            cert_dict["results"] = res_dict
        else:
            cert_dict["results"] = None
        conn.close()
        return cert_dict


class SQLiteAdapter:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.mode = "Local (SQLite)"
        self.init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        if not os.path.exists(self.db_path):
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                
                # Create local_auth table for local mock accounts
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS local_auth (
                        id VARCHAR(100) PRIMARY KEY,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        role VARCHAR(50) NOT NULL
                    )
                """)
                
                # Read schema.sql
                schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "schema.sql")
                with open(schema_path, "r") as f:
                    schema_sql = f.read()
                
                # Clean up PG-specific constraints/syntax that SQLite doesn't support
                # For SQLite, we omit ALTER TABLE ENABLE RLS and CREATE POLICY and PG triggers/functions.
                clean_sql = []
                for statement in schema_sql.split(";"):
                    stmt = statement.strip()
                    if not stmt:
                        continue
                    # Skip postgres specific commands
                    if any(x in stmt.upper() for x in ["ALTER TABLE", "ENABLE ROW LEVEL SECURITY", "CREATE POLICY", "CREATE OR REPLACE FUNCTION", "RETURNS BOOLEAN", "LANGUAGE PLPGSQL", "CREATE EXTENSION"]):
                        continue
                    if stmt.upper() == "END" or stmt.startswith("$$"):
                        continue
                    # Convert SERIAL to INTEGER PRIMARY KEY AUTOINCREMENT
                    stmt = stmt.replace("SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")
                    stmt = stmt.replace("TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP", "DATETIME DEFAULT CURRENT_TIMESTAMP")
                    stmt = stmt.replace("TIMESTAMPTZ", "DATETIME")
                    stmt = stmt.replace("UUID PRIMARY KEY", "VARCHAR(100) PRIMARY KEY")
                    stmt = stmt.replace("UUID REFERENCES", "VARCHAR(100) REFERENCES")
                    stmt = stmt.replace("NUMERIC(5,2)", "REAL")
                    clean_sql.append(stmt)

                for stmt in clean_sql:
                    try:
                        cursor.execute(stmt)
                    except Exception as e:
                        print(f"Error executing schema statement on SQLite: {e}\nStatement: {stmt}")
                
                conn.commit()

                # Seed default admin user in local_auth and admins tables
                admin_id = str(uuid.uuid4())
                admin_email = "admin@bcc.com"
                admin_name = "System Admin"
                admin_pass_hash = bcrypt.hashpw("admin123".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                
                try:
                    cursor.execute("INSERT OR IGNORE INTO local_auth (id, email, password_hash, role) VALUES (?, ?, ?, ?)",
                                   (admin_id, admin_email, admin_pass_hash, "admin"))
                    cursor.execute("INSERT OR IGNORE INTO admins (id, email, name) VALUES (?, ?, ?)",
                                   (admin_id, admin_email, admin_name))
                except Exception as e:
                    print(f"Error seeding default admin: {e}")

                # Seed initial questions if seed file exists
                seed_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "seed_data.sql")
                if os.path.exists(seed_path):
                    with open(seed_path, "r") as f:
                        seed_sql = f.read()
                    
                    for statement in seed_sql.split(";"):
                        stmt = statement.strip()
                        if stmt:
                            try:
                                cursor.execute(stmt)
                            except Exception as e:
                                print(f"Error seeding SQLite: {e}")
                    conn.commit()
            finally:
                conn.close()

    def _to_dict(self, row):
        return dict(row) if row else None

    def _to_list(self, rows):
        return [dict(row) for row in rows]

    # --- ADMINS ---
    def get_admin_by_id(self, admin_id):
        conn = self._get_connection()
        row = conn.execute("SELECT * FROM admins WHERE id = ?", (str(admin_id),)).fetchone()
        conn.close()
        return self._to_dict(row)

    def get_admin_by_email(self, email):
        conn = self._get_connection()
        row = conn.execute("SELECT * FROM admins WHERE email = ?", (email,)).fetchone()
        conn.close()
        return self._to_dict(row)

    def create_admin(self, admin_id, email, name):
        conn = self._get_connection()
        conn.execute("INSERT INTO admins (id, email, name) VALUES (?, ?, ?)", (str(admin_id), email, name))
        conn.commit()
        row = conn.execute("SELECT * FROM admins WHERE id = ?", (str(admin_id),)).fetchone()
        conn.close()
        return self._to_dict(row)

    # --- STUDENTS ---
    def get_student_by_id(self, student_id):
        conn = self._get_connection()
        row = conn.execute("SELECT * FROM students WHERE id = ?", (str(student_id),)).fetchone()
        conn.close()
        return self._to_dict(row)

    def get_student_by_email(self, email):
        conn = self._get_connection()
        row = conn.execute("SELECT * FROM students WHERE email = ?", (email,)).fetchone()
        conn.close()
        return self._to_dict(row)

    def get_student_by_roll(self, roll_number):
        conn = self._get_connection()
        row = conn.execute("SELECT * FROM students WHERE roll_number = ?", (roll_number,)).fetchone()
        conn.close()
        return self._to_dict(row)

    def create_student(self, student_id, email, name, roll_number, phone):
        conn = self._get_connection()
        conn.execute("INSERT INTO students (id, email, name, roll_number, phone) VALUES (?, ?, ?, ?, ?)", 
                     (str(student_id), email, name, roll_number, phone))
        conn.commit()
        row = conn.execute("SELECT * FROM students WHERE id = ?", (str(student_id),)).fetchone()
        conn.close()
        return self._to_dict(row)

    def get_all_students(self):
        conn = self._get_connection()
        rows = conn.execute("SELECT * FROM students ORDER BY created_at").fetchall()
        conn.close()
        return self._to_list(rows)

    def update_student(self, student_id, name, roll_number, phone):
        conn = self._get_connection()
        conn.execute("UPDATE students SET name = ?, roll_number = ?, phone = ? WHERE id = ?", 
                     (name, roll_number, phone, str(student_id)))
        conn.commit()
        row = conn.execute("SELECT * FROM students WHERE id = ?", (str(student_id),)).fetchone()
        conn.close()
        return self._to_dict(row)

    def delete_student(self, student_id):
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM students WHERE id = ?", (str(student_id),))
        conn.commit()
        count = cur.rowcount
        conn.close()
        return count > 0

    # --- QUESTION BANK ---
    def get_all_questions(self):
        conn = self._get_connection()
        rows = conn.execute("SELECT * FROM question_bank ORDER BY id").fetchall()
        conn.close()
        return self._to_list(rows)

    def get_questions_by_topic(self, topic):
        conn = self._get_connection()
        rows = conn.execute("SELECT * FROM question_bank WHERE topic = ?", (topic,)).fetchall()
        conn.close()
        return self._to_list(rows)

    def add_question(self, topic, question_text, question_type, option_a, option_b, option_c, option_d, correct_option, difficulty):
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("""INSERT INTO question_bank 
                       (topic, question_text, question_type, option_a, option_b, option_c, option_d, correct_option, difficulty) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
                    (topic, question_text, question_type, option_a, option_b, option_c, option_d, correct_option, difficulty))
        conn.commit()
        q_id = cur.lastrowid
        row = conn.execute("SELECT * FROM question_bank WHERE id = ?", (q_id,)).fetchone()
        conn.close()
        return self._to_dict(row)

    def update_question(self, question_id, topic, question_text, question_type, option_a, option_b, option_c, option_d, correct_option, difficulty):
        conn = self._get_connection()
        conn.execute("""UPDATE question_bank SET 
                       topic = ?, question_text = ?, question_type = ?, option_a = ?, option_b = ?, option_c = ?, option_d = ?, correct_option = ?, difficulty = ?
                       WHERE id = ?""", 
                    (topic, question_text, question_type, option_a, option_b, option_c, option_d, correct_option, difficulty, question_id))
        conn.commit()
        row = conn.execute("SELECT * FROM question_bank WHERE id = ?", (question_id,)).fetchone()
        conn.close()
        return self._to_dict(row)

    def delete_question(self, question_id):
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM question_bank WHERE id = ?", (question_id,))
        conn.commit()
        count = cur.rowcount
        conn.close()
        return count > 0

    def bulk_upload_questions(self, df):
        conn = self._get_connection()
        cur = conn.cursor()
        count = 0
        for _, row in df.iterrows():
            cur.execute("""INSERT INTO question_bank 
                           (topic, question_text, question_type, option_a, option_b, option_c, option_d, correct_option, difficulty) 
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
                        (row['topic'], row['question_text'], row['question_type'], 
                         row.get('option_a'), row.get('option_b'), row.get('option_c'), row.get('option_d'), 
                         row['correct_option'], row['difficulty']))
            count += 1
        conn.commit()
        conn.close()
        return count

    # --- EXAMS ---
    def get_all_exams(self):
        conn = self._get_connection()
        rows = conn.execute("SELECT * FROM exams ORDER BY created_at").fetchall()
        conn.close()
        return self._to_list(rows)

    def get_active_exams(self):
        conn = self._get_connection()
        rows = conn.execute("SELECT * FROM exams WHERE is_active = 1 ORDER BY created_at").fetchall()
        conn.close()
        return self._to_list(rows)

    def create_exam(self, title, description, duration_minutes, total_questions, passing_percentage, is_active, question_ids):
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO exams (title, description, duration_minutes, total_questions, passing_percentage, is_active) VALUES (?, ?, ?, ?, ?, ?)", 
                    (title, description, int(duration_minutes), int(total_questions), float(passing_percentage), 1 if is_active else 0))
        exam_id = cur.lastrowid
        
        for q_id in question_ids:
            cur.execute("INSERT INTO exam_questions (exam_id, question_id) VALUES (?, ?)", (exam_id, q_id))
        
        conn.commit()
        row = conn.execute("SELECT * FROM exams WHERE id = ?", (exam_id,)).fetchone()
        conn.close()
        return self._to_dict(row)

    def update_exam(self, exam_id, title, description, duration_minutes, total_questions, passing_percentage, is_active, question_ids):
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE exams SET title = ?, description = ?, duration_minutes = ?, total_questions = ?, passing_percentage = ?, is_active = ? WHERE id = ?", 
                    (title, description, int(duration_minutes), int(total_questions), float(passing_percentage), 1 if is_active else 0, exam_id))
        
        cur.execute("DELETE FROM exam_questions WHERE exam_id = ?", (exam_id,))
        for q_id in question_ids:
            cur.execute("INSERT INTO exam_questions (exam_id, question_id) VALUES (?, ?)", (exam_id, q_id))
        
        conn.commit()
        row = conn.execute("SELECT * FROM exams WHERE id = ?", (exam_id,)).fetchone()
        conn.close()
        return self._to_dict(row)

    def delete_exam(self, exam_id):
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM exams WHERE id = ?", (exam_id,))
        conn.commit()
        count = cur.rowcount
        conn.close()
        return count > 0

    def get_exam_questions(self, exam_id):
        conn = self._get_connection()
        rows = conn.execute("""SELECT q.* FROM question_bank q 
                               JOIN exam_questions eq ON q.id = eq.question_id 
                               WHERE eq.exam_id = ?""", (exam_id,)).fetchall()
        conn.close()
        return self._to_list(rows)

    # --- RESULTS & RESPONSES ---
    def create_result(self, student_id, exam_id, score, total_questions, percentage, grade, passed, started_at, submitted_at):
        conn = self._get_connection()
        cur = conn.cursor()
        
        started_str = started_at.isoformat() if isinstance(started_at, datetime) else str(started_at)
        submitted_str = submitted_at.isoformat() if isinstance(submitted_at, datetime) else str(submitted_at)
        
        cur.execute("""INSERT INTO results 
                       (student_id, exam_id, score, total_questions, percentage, grade, passed, started_at, submitted_at) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
                    (str(student_id), int(exam_id), int(score), int(total_questions), float(percentage), grade, 1 if passed else 0, started_str, submitted_str))
        conn.commit()
        result_id = cur.lastrowid
        row = conn.execute("SELECT * FROM results WHERE id = ?", (result_id,)).fetchone()
        conn.close()
        return self._to_dict(row)

    def save_responses(self, result_id, responses_list):
        conn = self._get_connection()
        cur = conn.cursor()
        count = 0
        for r in responses_list:
            cur.execute("""INSERT INTO responses (result_id, question_id, selected_option, is_correct) 
                           VALUES (?, ?, ?, ?)""", 
                        (result_id, r["question_id"], r["selected_option"], 1 if r["is_correct"] else 0))
            count += 1
        conn.commit()
        conn.close()
        return count

    def get_student_results(self, student_id):
        conn = self._get_connection()
        # Mock the join or perform manual join because JSON structures vary
        rows = conn.execute("""SELECT r.*, e.title as exam_title 
                               FROM results r 
                               JOIN exams e ON r.exam_id = e.id 
                               WHERE r.student_id = ? 
                               ORDER BY r.submitted_at DESC""", (str(student_id),)).fetchall()
        conn.close()
        # Add a synthetic "exams" nested dict to match supabase format
        results = []
        for r in rows:
            d = dict(r)
            d["exams"] = {"title": d["exam_title"]}
            results.append(d)
        return results

    def get_all_results(self):
        conn = self._get_connection()
        rows = conn.execute("""SELECT r.*, e.title as exam_title, s.name as student_name, s.roll_number as student_roll 
                               FROM results r 
                               JOIN exams e ON r.exam_id = e.id 
                               JOIN students s ON r.student_id = s.id 
                               ORDER BY r.submitted_at DESC""").fetchall()
        conn.close()
        results = []
        for r in rows:
            d = dict(r)
            d["exams"] = {"title": d["exam_title"]}
            d["students"] = {"name": d["student_name"], "roll_number": d["student_roll"]}
            results.append(d)
        return results

    def get_result_by_id(self, result_id):
        conn = self._get_connection()
        row_res = conn.execute("SELECT * FROM results WHERE id = ?", (result_id,)).fetchone()
        if not row_res:
            conn.close()
            return None
        res_dict = dict(row_res)
        
        row_exam = conn.execute("SELECT * FROM exams WHERE id = ?", (res_dict["exam_id"],)).fetchone()
        res_dict["exams"] = dict(row_exam) if row_exam else None
        
        row_stud = conn.execute("SELECT * FROM students WHERE id = ?", (res_dict["student_id"],)).fetchone()
        res_dict["students"] = dict(row_stud) if row_stud else None
        
        conn.close()
        return res_dict

    def get_result_responses(self, result_id):
        conn = self._get_connection()
        rows = conn.execute("""SELECT resp.*, q.topic, q.question_text, q.question_type, q.option_a, q.option_b, q.option_c, q.option_d, q.correct_option, q.difficulty 
                               FROM responses resp 
                               JOIN question_bank q ON resp.question_id = q.id 
                               WHERE resp.result_id = ?""", (result_id,)).fetchall()
        conn.close()
        responses = []
        for r in rows:
            d = dict(r)
            # Match Supabase query nesting structure: question_bank: { ... }
            d["question_bank"] = {
                "id": d["question_id"],
                "topic": d["topic"],
                "question_text": d["question_text"],
                "question_type": d["question_type"],
                "option_a": d["option_a"],
                "option_b": d["option_b"],
                "option_c": d["option_c"],
                "option_d": d["option_d"],
                "correct_option": d["correct_option"],
                "difficulty": d["difficulty"]
            }
            responses.append(d)
        return responses

    # --- TYPING RESULTS ---
    def create_typing_result(self, result_id, wpm, accuracy, passage_text, typed_text, passed):
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO typing_results (result_id, wpm, accuracy, passage_text, typed_text, passed)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (result_id, wpm, accuracy, passage_text, typed_text, passed))
        last_id = cur.lastrowid
        conn.commit()
        cur.execute("SELECT * FROM typing_results WHERE id = ?", (last_id,))
        row = cur.fetchone()
        conn.close()
        return self._to_dict(row)

    def get_typing_result_by_result_id(self, result_id):
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM typing_results WHERE result_id = ?", (result_id,))
        row = cur.fetchone()
        conn.close()
        return self._to_dict(row)

    # --- CERTIFICATES ---
    def get_certificate_by_result_id(self, result_id):
        conn = self._get_connection()
        row = conn.execute("SELECT * FROM certificates WHERE result_id = ?", (result_id,)).fetchone()
        conn.close()
        return self._to_dict(row)

    def create_certificate(self, certificate_id, student_id, result_id):
        conn = self._get_connection()
        conn.execute("INSERT INTO certificates (certificate_id, student_id, result_id) VALUES (?, ?, ?)", 
                     (certificate_id, str(student_id), result_id))
        conn.commit()
        row = conn.execute("SELECT * FROM certificates WHERE certificate_id = ?", (certificate_id,)).fetchone()
        conn.close()
        return self._to_dict(row)

    def get_certificate_by_id(self, certificate_id):
        conn = self._get_connection()
        row_cert = conn.execute("SELECT * FROM certificates WHERE certificate_id = ?", (certificate_id,)).fetchone()
        if not row_cert:
            conn.close()
            return None
        cert_dict = dict(row_cert)
        
        row_stud = conn.execute("SELECT * FROM students WHERE id = ?", (cert_dict["student_id"],)).fetchone()
        cert_dict["students"] = dict(row_stud) if row_stud else None
        
        # Get result and exam details
        row_res = conn.execute("SELECT * FROM results WHERE id = ?", (cert_dict["result_id"],)).fetchone()
        if row_res:
            res_dict = dict(row_res)
            row_exam = conn.execute("SELECT * FROM exams WHERE id = ?", (res_dict["exam_id"],)).fetchone()
            res_dict["exams"] = dict(row_exam) if row_exam else None
            cert_dict["results"] = res_dict
        else:
            cert_dict["results"] = None
            
        conn.close()
        return cert_dict
