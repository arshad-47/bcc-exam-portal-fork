-- Basic Computer Course Examination Portal - PostgreSQL Database Schema
-- Designed for Supabase PostgreSQL with Row Level Security (RLS)

-- Enable UUID extension if not enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ====================================================================
-- 1. ADMINS TABLE
-- ====================================================================
CREATE TABLE IF NOT EXISTS admins (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ====================================================================
-- 2. STUDENTS TABLE
-- ====================================================================
CREATE TABLE IF NOT EXISTS students (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    roll_number VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ====================================================================
-- 3. QUESTION BANK TABLE
-- ====================================================================
CREATE TABLE IF NOT EXISTS question_bank (
    id SERIAL PRIMARY KEY,
    topic VARCHAR(255) NOT NULL, -- e.g. "Computer Fundamentals", "Operating Systems", "MS Word", "Internet & Web"
    question_text TEXT NOT NULL,
    question_type VARCHAR(10) NOT NULL CHECK (question_type IN ('MCQ', 'TF')),
    option_a TEXT,
    option_b TEXT,
    option_c TEXT,
    option_d TEXT,
    correct_option VARCHAR(1) NOT NULL CHECK (correct_option IN ('A', 'B', 'C', 'D')),
    difficulty VARCHAR(20) NOT NULL CHECK (difficulty IN ('Easy', 'Medium', 'Hard')),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ====================================================================
-- 4. EXAMS TABLE
-- ====================================================================
CREATE TABLE IF NOT EXISTS exams (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    duration_minutes INT NOT NULL DEFAULT 30,
    total_questions INT NOT NULL DEFAULT 20,
    passing_percentage NUMERIC(5,2) NOT NULL DEFAULT 40.0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ====================================================================
-- 5. EXAM QUESTIONS TABLE (MAPPING)
-- ====================================================================
CREATE TABLE IF NOT EXISTS exam_questions (
    exam_id INT REFERENCES exams(id) ON DELETE CASCADE,
    question_id INT REFERENCES question_bank(id) ON DELETE CASCADE,
    PRIMARY KEY (exam_id, question_id)
);

-- ====================================================================
-- 6. RESULTS TABLE
-- ====================================================================
CREATE TABLE IF NOT EXISTS results (
    id SERIAL PRIMARY KEY,
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    exam_id INT REFERENCES exams(id) ON DELETE CASCADE,
    score INT NOT NULL DEFAULT 0,
    total_questions INT NOT NULL DEFAULT 0,
    percentage NUMERIC(5,2) NOT NULL DEFAULT 0.0,
    grade VARCHAR(2) NOT NULL, -- S, A, B, C, D, E, F
    passed BOOLEAN NOT NULL DEFAULT FALSE,
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ====================================================================
-- 7. RESPONSES TABLE
-- ====================================================================
CREATE TABLE IF NOT EXISTS responses (
    id SERIAL PRIMARY KEY,
    result_id INT REFERENCES results(id) ON DELETE CASCADE,
    question_id INT REFERENCES question_bank(id) ON DELETE CASCADE,
    selected_option VARCHAR(1) NOT NULL, -- A, B, C, D
    is_correct BOOLEAN NOT NULL
);

-- ====================================================================
-- 8. CERTIFICATES TABLE
-- ====================================================================
CREATE TABLE IF NOT EXISTS certificates (
    id SERIAL PRIMARY KEY,
    certificate_id VARCHAR(100) UNIQUE NOT NULL, -- Format: BCC-YYYYMMDD-XXXX
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    result_id INT REFERENCES results(id) ON DELETE CASCADE,
    issue_date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ====================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES (Supabase Specific)
-- ====================================================================

-- Enable RLS on all tables
ALTER TABLE admins ENABLE ROW LEVEL SECURITY;
ALTER TABLE students ENABLE ROW LEVEL SECURITY;
ALTER TABLE question_bank ENABLE ROW LEVEL SECURITY;
ALTER TABLE exams ENABLE ROW LEVEL SECURITY;
ALTER TABLE exam_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE results ENABLE ROW LEVEL SECURITY;
ALTER TABLE responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE certificates ENABLE ROW LEVEL SECURITY;

-- Helper function to check if a user is an admin
CREATE OR REPLACE FUNCTION is_admin() 
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM admins WHERE id = auth.uid()
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 1. admins RLS Policies
CREATE POLICY "Admins can manage admins" ON admins FOR ALL TO authenticated USING (is_admin());
CREATE POLICY "Users can read their own admin record" ON admins FOR SELECT TO authenticated USING (id = auth.uid());

-- 2. students RLS Policies
CREATE POLICY "Admins can manage students" ON students FOR ALL TO authenticated USING (is_admin());
CREATE POLICY "Students can view their own profile" ON students FOR SELECT TO authenticated USING (id = auth.uid());
CREATE POLICY "Allow public insert during student signup" ON students FOR INSERT TO anon, authenticated WITH CHECK (TRUE);

-- 3. question_bank RLS Policies
CREATE POLICY "Admins can manage question_bank" ON question_bank FOR ALL TO authenticated USING (is_admin());
CREATE POLICY "Students can read questions during exams" ON question_bank FOR SELECT TO authenticated USING (TRUE);

-- 4. exams RLS Policies
CREATE POLICY "Admins can manage exams" ON exams FOR ALL TO authenticated USING (is_admin());
CREATE POLICY "Students can view active exams" ON exams FOR SELECT TO authenticated USING (is_active = TRUE);

-- 5. exam_questions RLS Policies
CREATE POLICY "Admins can manage exam_questions" ON exam_questions FOR ALL TO authenticated USING (is_admin());
CREATE POLICY "Students can read exam_questions" ON exam_questions FOR SELECT TO authenticated USING (TRUE);

-- 6. results RLS Policies
CREATE POLICY "Admins can manage results" ON results FOR ALL TO authenticated USING (is_admin());
CREATE POLICY "Students can read their own results" ON results FOR SELECT TO authenticated USING (student_id = auth.uid());
CREATE POLICY "Students can insert their own results" ON results FOR INSERT TO authenticated WITH CHECK (student_id = auth.uid());
CREATE POLICY "Students can update their own results" ON results FOR UPDATE TO authenticated USING (student_id = auth.uid());

-- 7. responses RLS Policies
CREATE POLICY "Admins can manage responses" ON responses FOR ALL TO authenticated USING (is_admin());
CREATE POLICY "Students can manage their own responses" ON responses FOR ALL TO authenticated 
    USING (EXISTS (SELECT 1 FROM results WHERE id = responses.result_id AND student_id = auth.uid()));

-- 8. certificates RLS Policies
CREATE POLICY "Admins can manage certificates" ON certificates FOR ALL TO authenticated USING (is_admin());
CREATE POLICY "Students can read their own certificates" ON certificates FOR SELECT TO authenticated USING (student_id = auth.uid());
CREATE POLICY "Students can insert their own certificates" ON certificates FOR INSERT TO authenticated WITH CHECK (student_id = auth.uid());

-- ====================================================================
-- 9. TYPING RESULTS TABLE
-- ====================================================================
CREATE TABLE IF NOT EXISTS typing_results (
    id SERIAL PRIMARY KEY,
    result_id INT REFERENCES results(id) ON DELETE CASCADE,
    wpm INT NOT NULL DEFAULT 0,
    accuracy NUMERIC(5,2) NOT NULL DEFAULT 0.0,
    passage_text TEXT NOT NULL,
    typed_text TEXT NOT NULL,
    passed BOOLEAN NOT NULL DEFAULT FALSE
);

-- 9. typing_results RLS Policies
ALTER TABLE typing_results ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Admins can manage typing_results" ON typing_results FOR ALL TO authenticated USING (is_admin());
CREATE POLICY "Students can manage their own typing_results" ON typing_results FOR ALL TO authenticated 
    USING (EXISTS (SELECT 1 FROM results WHERE id = typing_results.result_id AND student_id = auth.uid()));
