from src.database import Database
import os

def update_exams():
    db = Database.get_client()
    conn = db._get_connection()
    cur = conn.cursor()
    
    try:
        # 1. Deactivate old exams
        cur.execute("UPDATE exams SET is_active = FALSE")
        
        # 2. Insert new unified exam
        cur.execute("""
            INSERT INTO exams (title, description, duration_minutes, total_questions, passing_percentage, is_active)
            VALUES (%s, %s, %s, %s, %s, TRUE)
            RETURNING id
        """, ("Unified BCC Certification Exam", "Comprehensive examination covering Computer Fundamentals, Windows OS, MS Word, MS Excel, MS PowerPoint, and Internet basics, along with a typing test.", 30, 26, 40.0))
        
        new_exam_id = cur.fetchone()[0]
        
        # 3. Get all questions
        cur.execute("SELECT id FROM question_bank")
        q_ids = [row[0] for row in cur.fetchall()]
        
        # 4. Insert all into exam_questions
        for q_id in q_ids:
            cur.execute("INSERT INTO exam_questions (exam_id, question_id) VALUES (%s, %s)", (new_exam_id, q_id))
            
        conn.commit()
        print(f"Successfully created unified exam with ID {new_exam_id} and {len(q_ids)} questions.")
        
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    update_exams()
