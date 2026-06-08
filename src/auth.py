import streamlit as st
import bcrypt
from postgrest.exceptions import APIError
import uuid
from datetime import datetime, timedelta
from src.config import Config
from src.database import Database

class Auth:
    @staticmethod
    def hash_password(password: str) -> str:
        # Generate salt and hash password
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    @staticmethod
    def check_password(password: str, hashed: str) -> bool:
        # Check password against hash
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    @staticmethod
    def login(email, password):
        db = Database.get_client()
        email = email.strip().lower()
        
        if Config.IS_SUPABASE_CONFIGURED and db.mode == "Supabase":
            # Supabase Auth Login
            try:
                auth_res = db.client.auth.sign_in_with_password({"email": email, "password": password})
                user = auth_res.user
                if not user:
                    raise Exception("Invalid email or password.")
                
                # Check role: Admin or Student?
                admin = db.get_admin_by_id(user.id)
                if admin:
                    role = "admin"
                    user_data = admin
                else:
                    student = db.get_student_by_id(user.id)
                    if student:
                        role = "student"
                        user_data = student
                    else:
                        raise Exception("Account found but not registered in Student/Admin record.")
                
                Auth._set_session(user.id, email, role, user_data)
                return True, role
            except Exception as e:
                # Get the detailed message
                msg = str(e)
                if "invalid login credentials" in msg.lower() or "invalid credentials" in msg.lower():
                    msg = "Invalid email or password."
                return False, msg
        else:
            # SQLite Mock Auth Login
            try:
                conn = db._get_connection()
                row = conn.execute("SELECT * FROM local_auth WHERE LOWER(email) = ?", (email,)).fetchone()
                conn.close()
                
                if not row:
                    return False, "Invalid email or password."
                
                local_user = dict(row)
                if not Auth.check_password(password, local_user["password_hash"]):
                    return False, "Invalid email or password."
                
                role = local_user["role"]
                if role == "admin":
                    user_data = db.get_admin_by_id(local_user["id"])
                else:
                    user_data = db.get_student_by_id(local_user["id"])
                
                if not user_data:
                    return False, "User details not found in database records."
                
                Auth._set_session(local_user["id"], email, role, user_data)
                return True, role
            except Exception as e:
                return False, f"Login error: {str(e)}"

    @staticmethod
    def signup_student(email, password, name, roll_number, phone):
        db = Database.get_client()
        email = email.strip().lower()
        roll_number = roll_number.strip().upper()
        
        # Validation checks
        if not email or not password or not name or not roll_number:
            return False, "All required fields must be filled."
            
        # Check if roll number or email already exists
        try:
            existing_stud_roll = db.get_student_by_roll(roll_number)
        except APIError as e:
            st.error(f"Supabase error checking roll number: {e}")
            existing_stud_roll = None
        if existing_stud_roll:
            return False, "A student with this Roll Number already exists."
        
        try:
            existing_stud_email = db.get_student_by_email(email)
        except APIError as e:
            st.error(f"Supabase error checking email: {e}")
            existing_stud_email = None
        if existing_stud_email:
            return False, "A student with this Email already exists."
            
        if Config.IS_SUPABASE_CONFIGURED and db.mode == "Supabase":
            try:
                # Signup in Supabase Auth
                auth_res = db.client.auth.sign_up({"email": email, "password": password})
                user = auth_res.user
                if not user:
                    raise Exception("Signup failed: No user returned from authentication server.")
                
                # Insert into students table
                db.create_student(user.id, email, name, roll_number, phone)
                return True, "Registration successful! You can now log in."
            except Exception as e:
                return False, f"Supabase Signup error: {str(e)}"
        else:
            # SQLite Mock Auth Signup
            try:
                user_id = str(uuid.uuid4())
                pass_hash = Auth.hash_password(password)
                
                conn = db._get_connection()
                # Check email in local_auth
                row = conn.execute("SELECT * FROM local_auth WHERE LOWER(email) = ?", (email,)).fetchone()
                if row:
                    conn.close()
                    return False, "Email already registered."
                
                # Insert credentials
                conn.execute("INSERT INTO local_auth (id, email, password_hash, role) VALUES (?, ?, ?, ?)",
                             (user_id, email, pass_hash, "student"))
                conn.commit()
                conn.close()
                
                # Insert student details
                db.create_student(user_id, email, name, roll_number, phone)
                return True, "Registration successful! You can now log in."
            except Exception as e:
                return False, f"Local Signup error: {str(e)}"

    @staticmethod
    def signup_admin(email, password, name):
        db = Database.get_client()
        email = email.strip().lower()
        
        if not email or not password or not name:
            return False, "All fields are required."
            
        if Config.IS_SUPABASE_CONFIGURED and db.mode == "Supabase":
            try:
                # Sign up in auth
                auth_res = db.client.auth.sign_up({"email": email, "password": password})
                user = auth_res.user
                if not user:
                    raise Exception("Signup failed.")
                
                # Create admin detail
                db.create_admin(user.id, email, name)
                return True, "Admin created successfully."
            except Exception as e:
                return False, str(e)
        else:
            try:
                user_id = str(uuid.uuid4())
                pass_hash = Auth.hash_password(password)
                
                conn = db._get_connection()
                conn.execute("INSERT INTO local_auth (id, email, password_hash, role) VALUES (?, ?, ?, ?)",
                             (user_id, email, pass_hash, "admin"))
                conn.commit()
                conn.close()
                
                db.create_admin(user_id, email, name)
                return True, "Admin created successfully."
            except Exception as e:
                return False, str(e)

    @staticmethod
    def reset_password(email):
        db = Database.get_client()
        email = email.strip().lower()
        if Config.IS_SUPABASE_CONFIGURED and db.mode == "Supabase":
            try:
                db.client.auth.reset_password_for_email(email)
                return True, "Password reset email sent. Please check your inbox."
            except Exception as e:
                return False, str(e)
        else:
            # SQLite Mock password reset simulation
            # In SQLite mock mode, we look up if user exists and simply mock a success message
            conn = db._get_connection()
            row = conn.execute("SELECT * FROM local_auth WHERE LOWER(email) = ?", (email,)).fetchone()
            conn.close()
            if row:
                return True, "[LOCAL MODE MOCK] A password reset link has been simulated for email: " + email
            return False, "No account found with this email address."

    @staticmethod
    def _set_session(user_id, email, role, user_data):
        st.session_state.authenticated = True
        st.session_state.user_id = user_id
        st.session_state.email = email
        st.session_state.role = role
        st.session_state.user_data = user_data
        st.session_state.last_activity = datetime.now()

    @staticmethod
    def logout():
        db = Database.get_client()
        if Config.IS_SUPABASE_CONFIGURED and db.mode == "Supabase":
            try:
                db.client.auth.sign_out()
            except:
                pass
        
        # Clear streamlit session states
        for key in ["authenticated", "user_id", "email", "role", "user_data", "last_activity", "exam_started", "exam_data", "exam_responses"]:
            if key in st.session_state:
                del st.session_state[key]

    @staticmethod
    def is_authenticated():
        return st.session_state.get("authenticated", False)

    @staticmethod
    def check_session_timeout():
        if not Auth.is_authenticated():
            return False
            
        last_activity = st.session_state.get("last_activity")
        if last_activity:
            elapsed = datetime.now() - last_activity
            if elapsed > timedelta(minutes=Config.SESSION_TIMEOUT_MINUTES):
                Auth.logout()
                st.warning("Session timed out due to inactivity. Please log in again.")
                st.rerun()
                return True
        st.session_state.last_activity = datetime.now()
        return False
