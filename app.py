import streamlit as st
st.set_page_config(
    page_title="Basic Computer Course Exam Portal",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

import pandas as pd
import plotly.express as px
import random
import io
from datetime import datetime, timedelta
from src.config import Config
from src.database import Database
from src.auth import Auth
from src.certificate import CertificateGenerator
from src.evaluation import EvaluationEngine
from src.utils import UIHelper

def main():
    # Inject Custom CSS styles
    UIHelper.inject_custom_css()
    
    # Initialize Database Connection
    db = Database.get_client()
    
    # Session Timeout Check (Logs out if inactive)
    if Auth.is_authenticated():
        if Auth.check_session_timeout():
            st.rerun()
            
    # Session State Initialization
    if "current_view" not in st.session_state:
        st.session_state.current_view = "Dashboard"
    if "exam_started" not in st.session_state:
        st.session_state.exam_started = False
    if "typing_phase" not in st.session_state:
        st.session_state.typing_phase = False
        
    # Route Page
    if not Auth.is_authenticated():
        render_login_screen()
    else:
        role = st.session_state.role
        if role == "admin":
            render_admin_portal()
        elif role == "student":
            if st.session_state.exam_started:
                render_exam_interface()
            elif st.session_state.get("typing_phase"):
                render_typing_test()
            else:
                render_student_portal()

# ====================================================================
# LOGIN & REGISTER SCREEN
# ====================================================================
def render_login_screen():
    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
    UIHelper.render_header(
        Config.INSTITUTE_NAME,
        f"{Config.COURSE_NAME} Examination Portal"
    )
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Show DB Mode status in a pill
        db = Database.get_client()
        status_color = "green" if db.mode == "Supabase" else "orange"
        st.markdown(
            f"<div style='text-align: center; margin-bottom: 1.5rem;'>"
            f"<span class='badge' style='background-color: {('#DCFCE7' if status_color == 'green' else '#FEF3C7')}; "
            f"color: {('#166534' if status_color == 'green' else '#92400E')};'>"
            f"Database Connection: {db.mode}</span></div>",
            unsafe_allow_html=True
        )
        
        tab_login, tab_forgot = st.tabs([
            "🔑 User Login", 
            "❓ Forgot Password"
        ])
        
        with tab_login:
            st.markdown("### Sign In to Your Account")
            login_email = st.text_input("Registered Email Address", key="login_email")
            login_password = st.text_input("Password", type="password", key="login_password")
            
            if st.button("Log In", type="primary", use_container_width=True):
                if login_email and login_password:
                    success, response = Auth.login(login_email, login_password)
                    if success:
                        st.success("Login successful! Redirecting...")
                        st.rerun()
                    else:
                        st.error(response)
                else:
                    st.warning("Please enter both email and password.")
                    
            if db.mode == "Local (SQLite)":
                st.info("💡 **Local Sandbox Mode**: You can log in using Admin credentials:\n"
                        "- **Email**: `admin@bcc.com` | **Password**: `admin123`\n"
                        "Or create a Student account in the Registration tab.")
                        
        # with tab_register:
        #     st.markdown("### Create Student Account")
        #     reg_name = st.text_input("Full Name", placeholder="e.g. John Doe")
        #     reg_email = st.text_input("Email Address", placeholder="e.g. john@example.com")
        #     reg_roll = st.text_input("Enrollment / Roll Number", placeholder="e.g. BCC-2026-101")
        #     reg_phone = st.text_input("Phone Number (Optional)", placeholder="e.g. +91 9876543210")
        #     reg_password = st.text_input("Choose Password", type="password", help="Minimum 6 characters")
        #     reg_confirm = st.text_input("Confirm Password", type="password")
            
        #     if st.button("Register Student", type="primary", use_container_width=True):
        #         if reg_password != reg_confirm:
        #             st.error("Passwords do not match.")
        #         elif len(reg_password) < 6:
        #             st.error("Password must be at least 6 characters long.")
        #         else:
        #             success, msg = Auth.signup_student(
        #                 email=reg_email,
        #                 password=reg_password,
        #                 name=reg_name,
        #                 roll_number=reg_roll,
        #                 phone=reg_phone
        #             )
        #             if success:
        #                 st.success(msg)
        #             else:
        #                 st.error(msg)
                        
        with tab_forgot:
            st.markdown("### Reset Password")
            forgot_email = st.text_input("Enter your registered email address")
            if st.button("Send Reset Link", type="primary", use_container_width=True):
                if forgot_email:
                    success, msg = Auth.reset_password(forgot_email)
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)
                else:
                    st.warning("Please enter your email.")

# ====================================================================
# STUDENT PORTAL
# ====================================================================
def render_student_portal():
    st.sidebar.markdown(f"### 🎓 Student Portal")
    st.sidebar.markdown(f"**Name:** {st.session_state.user_data['name']}")
    st.sidebar.markdown(f"**Roll No:** {st.session_state.user_data['roll_number']}")
    st.sidebar.markdown("---")
    
    options = {
        "Dashboard": "🏠 My Dashboard",
        "Exams": "📝 Available Exams",
        "Results": "📜 Previous Results"
    }
    
    selected_option = st.sidebar.radio(
        "Navigation Menu", 
        options=list(options.keys()), 
        format_func=lambda x: options[x]
    )
    st.session_state.current_view = selected_option
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Log Out", use_container_width=True):
        Auth.logout()
        st.rerun()
        
    # Content Area
    if st.session_state.current_view == "Dashboard":
        student_dashboard_view()
    elif st.session_state.current_view == "Exams":
        student_exams_view()
    elif st.session_state.current_view == "Results":
        student_results_view()

def student_dashboard_view():
    db = Database.get_client()
    st.markdown(f"## Welcome back, {st.session_state.user_data['name']}!")
    
    # Metric Summary
    results = db.get_student_results(st.session_state.user_id)
    exams_taken = len(results)
    passed_count = sum(1 for r in results if r["passed"])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        UIHelper.render_metric("Exams Attempted", exams_taken, "📝")
    with col2:
        UIHelper.render_metric("Exams Passed", passed_count, "🏆")
    with col3:
        pass_rate = f"{(passed_count/exams_taken*100):.1f}%" if exams_taken > 0 else "0.0%"
        UIHelper.render_metric("Passing Rate", pass_rate, "📈")
        
    st.markdown("### Profile Information")
    profile_html = f"""
    <div class='premium-card'>
        <table style='width: 100%; border-collapse: collapse;'>
            <tr><td style='padding: 8px; font-weight: bold; width: 30%; color: #4F46E5;'>Full Name:</td><td style='padding: 8px;'>{st.session_state.user_data['name']}</td></tr>
            <tr><td style='padding: 8px; font-weight: bold; color: #4F46E5;'>Email:</td><td style='padding: 8px;'>{st.session_state.user_data['email']}</td></tr>
            <tr><td style='padding: 8px; font-weight: bold; color: #4F46E5;'>Roll Number:</td><td style='padding: 8px;'>{st.session_state.user_data['roll_number']}</td></tr>
            <tr><td style='padding: 8px; font-weight: bold; color: #4F46E5;'>Phone:</td><td style='padding: 8px;'>{st.session_state.user_data['phone'] or 'N/A'}</td></tr>
            <tr><td style='padding: 8px; font-weight: bold; color: #4F46E5;'>Registered On:</td><td style='padding: 8px;'>{st.session_state.user_data['created_at']}</td></tr>
        </table>
    </div>
    """
    st.markdown(profile_html, unsafe_allow_html=True)
    
    # Recent Activities
    st.markdown("### Recent Exam Results")
    if results:
        recent_df = pd.DataFrame([
            {
                "Exam": r["exams"]["title"],
                "Score": f"{r['score']}/{r['total_questions']}",
                "Percentage": f"{r['percentage']:.2f}%",
                "Grade": r["grade"],
                "Status": "Passed" if r["passed"] else "Failed",
                "Date": str(r["submitted_at"])[:16]
            } for r in results[:3]
        ])
        st.dataframe(recent_df, hide_index=True)
    else:
        st.info("No exam history found. Navigate to 'Available Exams' to take your first test!")

def student_exams_view():
    db = Database.get_client()
    st.markdown("## Available Examinations")
    
    exams = db.get_active_exams()
    if not exams:
        st.info("There are currently no active exams available.")
        return
        
    for exam in exams:
        # Check if already attempted and passed
        results = db.get_student_results(st.session_state.user_id)
        attempted = False
        passed = False
        for r in results:
            if r["exam_id"] == exam["id"]:
                attempted = True
                if r["passed"]:
                    passed = True
                    
        status_html = ""
        if passed:
            status_html = "<span class='badge badge-pass'>PASSED & CERTIFIED</span>"
        elif attempted:
            status_html = "<span class='badge badge-info'>ATTEMPTED</span>"
        else:
            status_html = "<span class='badge badge-info'>NEW</span>"
            
        desc = exam['description'] or "No description provided."
        col_content = f"""
        <div class="premium-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h4 style="margin:0; color:#1E3A8A;">{exam['title']}</h4>
                {status_html}
            </div>
            <p style="margin: 0.5rem 0; color:#475569; font-size:0.95rem;">{desc}</p>
            <div style="display: flex; gap: 1.5rem; font-size: 0.9rem; color: #64748B;">
                <span>⏱️ <b>Duration:</b> {exam['duration_minutes']} Mins</span>
                <span>❓ <b>Questions:</b> {exam['total_questions']} MCQs/TFs</span>
                <span>🎯 <b>Passing Target:</b> {exam['passing_percentage']}%</span>
            </div>
        </div>
        """
        st.markdown(col_content, unsafe_allow_html=True)
        
        # Start button
        col_left, col_btn = st.columns([5, 1])
        with col_btn:
            btn_label = "Retake Exam" if attempted else "Start Exam"
            if st.button(btn_label, key=f"start_exam_{exam['id']}", type="primary", use_container_width=True):
                # Retrieve questions
                questions = db.get_exam_questions(exam["id"])
                
                if len(questions) < exam["total_questions"]:
                    st.error(f"Cannot start exam. Admin configured {exam['total_questions']} questions, but the question pool only has {len(questions)} items. Please contact admin.")
                else:
                    # Setup Exam Session State variables
                    random.seed()
                    # Randomized question selection
                    selected_qs = random.sample(questions, k=exam["total_questions"])
                    
                    st.session_state.exam_started = True
                    st.session_state.exam_data = exam
                    st.session_state.exam_questions = selected_qs
                    st.session_state.exam_responses = {}
                    st.session_state.exam_start_time = datetime.now()
                    st.session_state.exam_flagged_questions = set()
                    st.session_state.exam_visited_questions = {selected_qs[0]["id"]}
                    st.session_state.current_question_index = 0
                    st.rerun()
        st.markdown("<hr style='margin: 1rem 0; border:0; border-top:1px solid #E2E8F0;'/>", unsafe_allow_html=True)

def student_results_view():
    db = Database.get_client()
    st.markdown("## My Examination Performance & Certificates")
    
    results = db.get_student_results(st.session_state.user_id)
    if not results:
        st.info("No exam attempts found.")
        return
        
    for r in results:
        passed = r["passed"]
        badge_class = "badge-pass" if passed else "badge-fail"
        status_text = "PASSED" if passed else "FAILED"
        
        col1, col2 = st.columns([4, 1])
        with col1:
            # Fetch typing test result for this attempt
            typing_result = db.get_typing_result_by_result_id(r["id"])
            typing_badge = ""
            if typing_result:
                t_wpm = typing_result.get("wpm", 0)
                t_acc = typing_result.get("accuracy", 0)
                typing_badge = f"<span>⌨️ <b>Typing:</b> {t_wpm} WPM ({t_acc:.0f}% acc)</span>"

            st.markdown(f"""
            <div class='premium-card' style='margin-bottom:0px;'>
                <div style='display:flex; justify-content:space-between;'>
                    <span style='font-size:1.15rem; font-weight:bold; color:#1E3A8A;'>{r['exams']['title']}</span>
                    <span class='badge {badge_class}'>{status_text}</span>
                </div>
                <div style='margin-top:0.5rem; display:flex; gap:2rem; font-size:0.95rem; color:#475569; flex-wrap:wrap;'>
                    <span>📅 <b>Submitted on:</b> {str(r['submitted_at'])[:16]}</span>
                    <span>📈 <b>Percentage:</b> {r['percentage']:.2f}%</span>
                    <span>🏅 <b>Grade:</b> {r['grade']}</span>
                    <span>🎯 <b>Score:</b> {r['score']}/{r['total_questions']}</span>
                    {typing_badge}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            if passed:
                # Certificate Generation
                cert = db.get_certificate_by_result_id(r["id"])
                
                if not cert:
                    # Dynamically register certificate if somehow missing
                    cert_id = CertificateGenerator.generate_cert_id(r["id"])
                    db.create_certificate(cert_id, st.session_state.user_id, r["id"])
                    cert = {"certificate_id": cert_id}
                    
                # Setup verification link
                base_url = "https://bcc-exam-phoenix-tech.streamlit.app" # Default local port
                verification_url = f"{base_url}/?verify={cert['certificate_id']}"

                typing_result = typing_result or {}
                cert_data = {
                    "certificate_id": cert["certificate_id"],
                    "student_name": st.session_state.user_data["name"],
                    "roll_number": st.session_state.user_data["roll_number"],
                    "exam_title": r["exams"]["title"],
                    "percentage": r["percentage"],
                    "grade": r["grade"],
                    "issue_date": str(r["submitted_at"])[:10],
                    "verification_url": verification_url,
                    "typing_wpm": typing_result.get("wpm"),
                    "typing_accuracy": typing_result.get("accuracy")
                }
                
                try:
                    pdf_io = CertificateGenerator.create_pdf(cert_data)
                    st.download_button(
                        label="⬇️ Certificate",
                        data=pdf_io,
                        file_name=f"BCC_Certificate_{cert['certificate_id']}.pdf",
                        mime="application/pdf",
                        key=f"dl_btn_{r['id']}",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Error generating PDF: {e}")
            else:
                    st.button("❌ Certificate", disabled=True, key=f"dl_dis_{r['id']}", use_container_width=True)
        st.markdown("<div style='margin-bottom:1.5rem;'></div>", unsafe_allow_html=True)

# ====================================================================
# EXAM ENGINE INTERFACE (FULL-SCREEN EXPERIENCE)
# ====================================================================
def render_exam_interface():
    db = Database.get_client()
    exam = st.session_state.exam_data
    questions = st.session_state.exam_questions
    responses = st.session_state.exam_responses
    flagged = st.session_state.exam_flagged_questions
    visited = st.session_state.exam_visited_questions
    current_idx = st.session_state.current_question_index
    
    # Calculate Timer
    elapsed = datetime.now() - st.session_state.exam_start_time
    total_seconds = exam["duration_minutes"] * 60
    remaining_seconds = total_seconds - elapsed.total_seconds()
    
    # Automatically Submit if time has run out
    if remaining_seconds <= 0:
        st.error("⏰ Time is up! Submitting your exam responses automatically...")
        submit_student_exam(db, exam, questions, responses)
        st.rerun()
        return

    # Convert remaining seconds to minutes and seconds
    mins, secs = divmod(int(remaining_seconds), 60)
    timer_display = f"⏱️ {mins:02d}:{secs:02d}"
    
    # Sidebar: Lock operations, display timer and grid
    st.sidebar.markdown(f"### 📝 EXAM ACTIVE")
    st.sidebar.markdown(f"**Exam:** {exam['title']}")
    
    # Timer with visual coloring
    timer_color = "red" if mins < 5 else "#1E3A8A"
    st.sidebar.markdown(f"""
        <div style='background-color:#F8FAFC; border: 2px solid {timer_color}; border-radius:10px; padding:12px; text-align:center;'>
            <span style='font-size:1.8rem; font-weight:700; color:{timer_color};'>{timer_display}</span>
        </div>
    """, unsafe_allow_html=True)
    
    # Progress bar
    answered_count = len(responses)
    progress_val = answered_count / len(questions)
    st.sidebar.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
    st.sidebar.progress(progress_val)
    st.sidebar.text(f"Answered: {answered_count} / {len(questions)}")
    
    # Sidebar Navigator Grid
    st.sidebar.markdown("---")
    st.sidebar.markdown("#### Question Navigator")
    
    # Create rows of 5 buttons
    cols_grid = st.sidebar.columns(5)
    for idx, q in enumerate(questions):
        col_item = cols_grid[idx % 5]
        q_id = q["id"]
        
        # Color coding state
        if idx == current_idx:
            btn_style = "border: 2px solid #4F46E5; background-color: #EEF2FF; color: #4F46E5; font-weight: bold;"
        elif q_id in responses:
            btn_style = "background-color: #DCFCE7; color: #166534; border: 1px solid #BBF7D0;"
        elif q_id in flagged:
            btn_style = "background-color: #FEF3C7; color: #92400E; border: 1px solid #FDE68A;"
        elif q_id in visited:
            btn_style = "background-color: #F1F5F9; color: #475569; border: 1px solid #CBD5E1;"
        else:
            btn_style = "background-color: #F8FAFC; color: #94A3B8; border: 1px solid #E2E8F0;"
            
        with col_item:
            if st.button(f"{idx+1}", key=f"nav_grid_{idx}", use_container_width=True):
                st.session_state.current_question_index = idx
                st.session_state.exam_visited_questions.add(questions[idx]["id"])
                st.rerun()
                
    st.sidebar.markdown("---")
    st.sidebar.warning("⚠️ Do not refresh or exit the browser window. Doing so will reset your current progress.")
    
    # Main Exam Engine Screen
    st.title(f"💻 BCC Certification Exam Engine")
    st.subheader(exam["title"])
    
    if current_idx >= len(questions):
        current_idx = len(questions) - 1
        st.session_state.current_question_index = current_idx
    elif current_idx < 0:
        current_idx = 0
        st.session_state.current_question_index = current_idx

    q_curr = questions[current_idx]
    q_id_curr = q_curr["id"]
    
    st.markdown(f"""
        <div style='background-color:#EEF2FF; border-left:4px solid #4F46E5; padding:8px 12px; margin-bottom:15px; display:flex; justify-content:space-between;'>
            <span style='color:#312E81; font-weight:bold;'>QUESTION {current_idx+1} OF {len(questions)}</span>
            <span class='badge' style='background-color:#E0F2FE; color:#0369A1;'>Topic: {q_curr['topic']}</span>
            <span class='badge' style='background-color:#F1F5F9; color:#475569;'>Difficulty: {q_curr['difficulty']}</span>
        </div>
    """, unsafe_allow_html=True)
    
    # Question presentation card
    st.markdown(f"""
        <div class='premium-card' style='margin-bottom: 20px;'>
            <p style='font-size:1.25rem; font-weight:600; color:#1E293B; line-height:1.6;'>{q_curr['question_text']}</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Input Selection
    current_selected = responses.get(q_id_curr, "")
    
    if q_curr["question_type"] == "MCQ":
        opts = {
            "A": q_curr['option_a'],
            "B": q_curr['option_b'],
            "C": q_curr['option_c'],
            "D": q_curr['option_d']
        }
        
        import random
        keys = list(opts.keys())
        rng = random.Random(q_curr['id'] + int(st.session_state.exam_start_time.timestamp()))
        rng.shuffle(keys)
        
        # We find index of current selection for radio
        radio_idx = keys.index(current_selected) if current_selected in keys else None
        
        selected_key = st.radio(
            "Select the correct answer:",
            options=keys,
            format_func=lambda x: opts[x],
            index=radio_idx,
            key=f"q_opt_select_{q_id_curr}"
        )
        # Update answer
        if selected_key:
            st.session_state.exam_responses[q_id_curr] = selected_key
            
    elif q_curr["question_type"] == "TF":
        opts = {
            "A": "True",
            "B": "False"
        }
        radio_idx = list(opts.keys()).index(current_selected) if current_selected in opts else None
        
        selected_key = st.radio(
            "Select True or False:",
            options=list(opts.keys()),
            format_func=lambda x: opts[x],
            index=radio_idx,
            key=f"q_tf_select_{q_id_curr}"
        )
        if selected_key:
            st.session_state.exam_responses[q_id_curr] = selected_key
            
    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
    
    # Navigation controls
    col_nav1, col_nav2, col_nav3, col_nav4 = st.columns([1, 1, 1, 1])
    
    with col_nav1:
        if st.button("⬅️ Previous Question", disabled=(current_idx <= 0), use_container_width=True):
            if st.session_state.current_question_index > 0:
                st.session_state.current_question_index -= 1
                st.session_state.exam_visited_questions.add(questions[st.session_state.current_question_index]["id"])
                st.rerun()
            
    with col_nav2:
        if st.button("Next Question ➡️", disabled=(current_idx >= len(questions) - 1), use_container_width=True):
            if st.session_state.current_question_index < len(questions) - 1:
                st.session_state.current_question_index += 1
                st.session_state.exam_visited_questions.add(questions[st.session_state.current_question_index]["id"])
                st.rerun()
            
    with col_nav3:
        flag_btn_label = "Unflag Question 🏳️" if q_id_curr in flagged else "Flag for Review 🏴"
        if st.button(flag_btn_label, use_container_width=True):
            if q_id_curr in flagged:
                st.session_state.exam_flagged_questions.remove(q_id_curr)
            else:
                st.session_state.exam_flagged_questions.add(q_id_curr)
            st.rerun()
            
    with col_nav4:
        if st.button("🧹 Clear Selection", use_container_width=True):
            if q_id_curr in st.session_state.exam_responses:
                del st.session_state.exam_responses[q_id_curr]
            st.rerun()
            
    # Submit Block
    st.markdown("<hr style='margin: 2rem 0;'/>", unsafe_allow_html=True)
    col_sub_left, col_sub_btn = st.columns([4, 1])
    with col_sub_btn:
        if st.button("🚨 Submit Exam", type="primary", use_container_width=True):
            submit_student_exam(db, exam, questions, responses)
            st.rerun()

def submit_student_exam(db, exam, questions, responses):
    # Call Evaluation Engine
    eval_results = EvaluationEngine.evaluate_exam(questions, responses, exam["passing_percentage"])
    
    # Save results to DB
    result = db.create_result(
        student_id=st.session_state.user_id,
        exam_id=exam["id"],
        score=eval_results["score"],
        total_questions=eval_results["total_questions"],
        percentage=eval_results["percentage"],
        grade=eval_results["grade"],
        passed=eval_results["passed"],
        started_at=st.session_state.exam_start_time,
        submitted_at=datetime.now()
    )
    
    # Save detail responses
    if result:
        db.save_responses(result["id"], eval_results["response_details"])
        
        # If passed, register certificate (will be updated with typing data later)
        if eval_results["passed"]:
            cert_id = CertificateGenerator.generate_cert_id(result["id"])
            db.create_certificate(cert_id, st.session_state.user_id, result["id"])
            
    # Store MCQ results in session and transition to Typing Test phase
    st.session_state.exam_started = False
    st.session_state.typing_phase = True
    st.session_state.mcq_results = {
        "title": exam["title"],
        "score": eval_results["score"],
        "total_questions": eval_results["total_questions"],
        "percentage": eval_results["percentage"],
        "grade": eval_results["grade"],
        "passed": eval_results["passed"],
        "topic_analysis": eval_results["topic_analysis"],
        "bcc_grade": eval_results.get("bcc_grade", "N/A"),
        "msoffice_grade": eval_results.get("msoffice_grade", "N/A"),
        "result_id": result["id"] if result else None
    }
    st.session_state.typing_start_time = datetime.now()



# Typing Test passage
TYPING_PASSAGE = (
    "A computer is an electronic device that processes data according to a set of instructions "
    "called a program. Computers are used in many fields such as science, education, business, "
    "and communication. The basic components of a computer include the central processing unit, "
    "memory, storage devices, and input and output peripherals. Operating systems manage hardware "
    "and software resources and provide common services for computer programs. The internet has "
    "transformed the way people communicate, access information, and conduct business worldwide."
)
TYPING_DURATION_MINUTES = 1.0

def render_typing_test():
    db = Database.get_client()
    mcq = st.session_state.get("mcq_results", {})

    # Calculate time remaining for the typing test
    elapsed = datetime.now() - st.session_state.get("typing_start_time", datetime.now())
    total_seconds = int(TYPING_DURATION_MINUTES * 60)
    remaining_seconds = max(0, total_seconds - int(elapsed.total_seconds()))
    mins, secs = divmod(remaining_seconds, 60)
    timer_color = "red" if mins < 1 else "#1E3A8A"

    # Sidebar info
    st.sidebar.markdown("### ⌨️ TYPING TEST")
    st.sidebar.markdown(f"**MCQ Phase:** ✅ Completed")
    st.sidebar.markdown(f"**MCQ Grade:** `{mcq.get('grade', 'N/A')}` ({mcq.get('percentage', 0):.2f}%)")
    
    # We use a streamlit component for a live ticking timer without refreshing the page
    import streamlit.components.v1 as components
    timer_html = f"""
        <div style="background-color:#F8FAFC; border:2px solid {timer_color}; border-radius:10px; padding:12px; text-align:center; font-family: sans-serif;">
            <span id="timer" style="font-size:1.8rem; font-weight:700; color:{timer_color};">⏱️ {mins:02d}:{secs:02d}</span>
        </div>
        <script>
            var timeLeft = {remaining_seconds};
            var timerEl = document.getElementById("timer");
            var interval = setInterval(function() {{
                timeLeft--;
                if(timeLeft <= 0) {{
                    clearInterval(interval);
                    timerEl.innerHTML = "⏱️ 00:00";
                }} else {{
                    var m = Math.floor(timeLeft / 60);
                    var s = timeLeft % 60;
                    timerEl.innerHTML = "⏱️ " + (m < 10 ? "0" + m : m) + ":" + (s < 10 ? "0" + s : s);
                }}
            }}, 1000);
        </script>
    """
    with st.sidebar:
        import base64
        b64_html = base64.b64encode(timer_html.encode('utf-8')).decode('utf-8')
        components.iframe(f"data:text/html;base64,{b64_html}", height=80)
        
    st.sidebar.markdown("---")
    st.sidebar.info("Type the passage exactly as shown. Accuracy and speed both count!")

    # Auto-submit when time is up
    if remaining_seconds <= 0:
        typed = st.session_state.get("typing_input_text", "")
        actual_elapsed = min(elapsed.total_seconds() / 60.0, TYPING_DURATION_MINUTES)
        _submit_typing_test(db, mcq, TYPING_PASSAGE, typed, actual_elapsed)
        st.rerun()
        return

    st.markdown("## ⌨️ Typing Test — Phase 2")
    st.markdown("""
    <div style='background-color:#EFF6FF; border-left:4px solid #3B82F6; padding:12px 16px; border-radius:6px; margin-bottom:1rem;'>
        <b>Instructions:</b> Type the passage below in the text box exactly as shown. 
        Your speed (WPM) and accuracy will be measured. Minimum required: <b>20 WPM</b> with <b>95% accuracy</b>.
    </div>
    """, unsafe_allow_html=True)

    # Passage display
    st.markdown(f"""
    <div style='background-color:#F1F5F9; border:1px solid #CBD5E1; border-radius:8px; padding:20px; 
                font-family:Georgia, serif; font-size:1.05rem; line-height:1.8; color:#1E293B; margin-bottom:1.5rem;'>
        {TYPING_PASSAGE}
    </div>
    """, unsafe_allow_html=True)

    typed_text = st.text_area(
        "Start typing here:",
        key="typing_input_text",
        height=180,
        placeholder="Begin typing the passage above...",
        help="Type exactly as shown. Spelling and punctuation matter."
    )

    st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)

    col_skip, col_submit = st.columns([3, 1])
    with col_skip:
        if st.button("⏭️ Skip Typing Test (Score 0 WPM)", use_container_width=True):
            _submit_typing_test(db, mcq, TYPING_PASSAGE, "", TYPING_DURATION_MINUTES)
            st.rerun()
    with col_submit:
        if st.button("✅ Submit Typing Test", type="primary", use_container_width=True):
            actual_elapsed_min = min(elapsed.total_seconds() / 60.0, TYPING_DURATION_MINUTES)
            _submit_typing_test(db, mcq, TYPING_PASSAGE, typed_text or "", actual_elapsed_min)
            st.rerun()

def _submit_typing_test(db, mcq_results, passage, typed_text, duration_minutes):
    """Evaluate typing test, persist result, then set up final results screen."""
    typing_eval = EvaluationEngine.evaluate_typing_test(passage, typed_text, duration_minutes)
    wpm = typing_eval["wpm"]
    accuracy = typing_eval["accuracy"]
    # Pass criteria: ≥20 WPM and ≥95% accuracy
    typing_passed = wpm >= 20 and accuracy >= 95.0

    result_id = mcq_results.get("result_id")
    if result_id:
        try:
            db.create_typing_result(
                result_id=result_id,
                wpm=wpm,
                accuracy=accuracy,
                passage_text=passage,
                typed_text=typed_text,
                passed=typing_passed
            )
        except Exception as e:
            pass  # Non-critical; results screen still shows

    # Transition to final results screen
    st.session_state.typing_phase = False
    st.session_state.last_exam_results = {
        **mcq_results,
        "typing_wpm": wpm,
        "typing_accuracy": accuracy,
        "typing_passed": typing_passed
    }
    st.session_state.current_view = "ExamResultScreen"

# Post Exam evaluation results display

def show_exam_results_screen():
    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
    res = st.session_state.get("last_exam_results")
    if not res:
        st.session_state.current_view = "Dashboard"
        st.rerun()
        return
        
    db = Database.get_client()
    
    passed = res["passed"]
    grade_color = "#10B981" if passed else "#EF4444"
    status_text = "CONGRATULATIONS! YOU PASSED" if passed else "EXAM FAILED"
    status_bg = "#DCFCE7" if passed else "#FEE2E2"
    status_fg = "#166534" if passed else "#991B1B"
    
    UIHelper.render_header(
        res['title'],
        "Examination Assessment Report"
    )
    
    col_l, col_r = st.columns([2, 1])
    
    with col_l:
        st.markdown(f"""
        <div style='background-color: {status_bg}; border-left: 6px solid {grade_color}; border-radius: 8px; padding: 20px; margin-bottom: 20px;'>
            <h3 style='margin:0; color: {status_fg}; font-weight:700;'>{status_text}</h3>
            <p style='margin: 5px 0 0 0; color: {status_fg}; font-size:1.1rem;'>
                Course: {Config.COURSE_NAME} | Grade Awarded: <b>{res['grade']}</b>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Display Plotly breakdown
        st.markdown("### Topic-wise Accuracy Analysis")
        topic_analysis = res["topic_analysis"]
        if topic_analysis:
            rows = []
            for topic, stats in topic_analysis.items():
                rows.append({
                    "Topic": topic,
                    "Total Questions": stats["total"],
                    "Correct Answers": stats["correct"],
                    "Accuracy (%)": stats["accuracy"]
                })
            df_topic = pd.DataFrame(rows)
            
            # Generate horizontal bar plot for topics
            fig = px.bar(
                df_topic,
                x="Accuracy (%)",
                y="Topic",
                orientation="h",
                labels={"Accuracy (%)": "Accuracy (%)", "Topic": "Topics"},
                color="Accuracy (%)",
                color_continuous_scale=["#EF4444", "#F59E0B", "#10B981"],
                range_x=[0, 100]
            )
            fig.update_layout(
                coloraxis_showscale=False,
                margin=dict(t=10, b=10, l=10, r=10),
                height=220,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig)
        else:
            st.info("No topic-wise details available.")
            
    with col_r:
        st.markdown("### Performance Metrics")
        
        # Render MCQ metrics
        UIHelper.render_metric("Final Score", f"{res['score']} / {res['total_questions']}", "🎯")
        UIHelper.render_metric("Score Percentage", f"{res['percentage']:.2f}%", "📊")
        
        # Render Module metrics
        if res.get("bcc_grade") and res.get("bcc_grade") != "N/A":
            st.markdown("---")
            st.markdown("#### 📚 Module Performance")
            UIHelper.render_metric("BCC Module Grade", res.get("bcc_grade", "N/A"), "🖥️")
            UIHelper.render_metric("MS Office Module Grade", res.get("msoffice_grade", "N/A"), "📄")

        # Render Typing Test metrics
        typing_wpm = res.get("typing_wpm")
        typing_accuracy = res.get("typing_accuracy")
        typing_passed_flag = res.get("typing_passed", False)
        if typing_wpm is not None:
            st.markdown("---")
            st.markdown("#### ⌨️ Typing Test Results")
            UIHelper.render_metric("Typing Speed", f"{typing_wpm} WPM", "⌨️")
            UIHelper.render_metric("Typing Accuracy", f"{typing_accuracy:.1f}%", "🎯")
            if typing_passed_flag:
                st.success("✅ Typing Test Passed!")
            else:
                st.error("❌ Typing Test: Below minimum (20 WPM, 95% accuracy)")
        
        # Certificate download if passed
        if passed and res.get("result_id"):
            cert = db.get_certificate_by_result_id(res["result_id"])
            if not cert:
                cert_id = CertificateGenerator.generate_cert_id(res["result_id"])
                db.create_certificate(cert_id, st.session_state.user_id, res["result_id"])
                cert = {"certificate_id": cert_id}
                
            base_url = "https://bcc-exam-phoenix-tech.streamlit.app" # Default local port
            verification_url = f"{base_url}/?verify={cert['certificate_id']}"
            
            cert_data = {
                "certificate_id": cert["certificate_id"],
                "student_name": st.session_state.user_data["name"],
                "roll_number": st.session_state.user_data["roll_number"],
                "exam_title": res["title"],
                "percentage": res["percentage"],
                "grade": res["grade"],
                "issue_date": datetime.now().strftime("%Y-%m-%d"),
                "verification_url": verification_url,
                "typing_wpm": res.get("typing_wpm"),
                "typing_accuracy": res.get("typing_accuracy"),
                "bcc_grade": res.get("bcc_grade"),
                "msoffice_grade": res.get("msoffice_grade")
            }
            
            try:
                pdf_io = CertificateGenerator.create_pdf(cert_data)
                st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
                st.download_button(
                    label="🎓 Download Certificate PDF",
                    data=pdf_io,
                    file_name=f"BCC_Certificate_{cert['certificate_id']}.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Error compiling certificate: {e}")

                
    st.markdown("<hr/>", unsafe_allow_html=True)
    if st.button("🔙 Return to Student Dashboard", use_container_width=True):
        if "last_exam_results" in st.session_state:
            del st.session_state["last_exam_results"]
        st.session_state.current_view = "Dashboard"
        st.rerun()

# ====================================================================
# ADMIN PORTAL
# ====================================================================
def render_admin_portal():
    st.sidebar.markdown(f"### ⚙️ Admin Console")
    st.sidebar.markdown(f"**Admin:** {st.session_state.user_data['name']}")
    st.sidebar.markdown("---")
    
    options = {
        "Dashboard": "📊 Dashboard & Analytics",
        "Students": "👥 Student Management",
        "Questions": "📚 Question Bank",
        "Exams": "📝 Exam Management",
        "Reports": "📑 Performance Reports"
    }
    
    selected_option = st.sidebar.radio(
        "Console Menu",
        options=list(options.keys()),
        format_func=lambda x: options[x]
    )
    st.session_state.current_view = selected_option
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Log Out", use_container_width=True):
        Auth.logout()
        st.rerun()
        
    # Content Area
    if st.session_state.current_view == "Dashboard":
        admin_dashboard_view()
    elif st.session_state.current_view == "Students":
        admin_students_view()
    elif st.session_state.current_view == "Questions":
        admin_questions_view()
    elif st.session_state.current_view == "Exams":
        admin_exams_view()
    elif st.session_state.current_view == "Reports":
        admin_reports_view()

def admin_dashboard_view():
    db = Database.get_client()
    st.markdown("## Admin Dashboard & Analytics")
    
    # Query details
    students = db.get_all_students()
    questions = db.get_all_questions()
    exams = db.get_all_exams()
    results_raw = db.get_all_results()
    
    tot_students = len(students)
    tot_questions = len(questions)
    tot_exams = len(exams)
    tot_attempts = len(results_raw)
    
    # Render stats row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        UIHelper.render_metric("Total Students", tot_students, "👥")
    with col2:
        UIHelper.render_metric("Question Pool", tot_questions, "📚")
    with col3:
        UIHelper.render_metric("Exams Created", tot_exams, "📝")
    with col4:
        UIHelper.render_metric("Exams Attempted", tot_attempts, "📋")
        
    st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)
    
    if tot_attempts > 0:
        results_df = pd.DataFrame(results_raw)
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            fig_pie = UIHelper.plot_pass_fail_pie(results_df)
            if fig_pie:
                st.plotly_chart(fig_pie)
        with col_c2:
            fig_trends = UIHelper.plot_exam_trends_line(results_df)
            if fig_trends:
                st.plotly_chart(fig_trends)
                
        # Leaderboard rankings
        st.markdown("### 🏆 Top Performing Student Leaderboard")
        # Group by student name and average percentage
        leaderboard = results_df.groupby(["student_id"]).agg({
            "percentage": "mean",
            "score": "sum",
            "total_questions": "sum"
        }).reset_index()
        
        # Merge student metadata
        student_meta = pd.DataFrame([{"student_id": s["id"], "name": s["name"], "roll": s["roll_number"]} for s in students])
        if not student_meta.empty:
            rankings = pd.merge(leaderboard, student_meta, on="student_id")
            rankings = rankings.rename(columns={
                "name": "Student Name",
                "roll": "Roll Number",
                "percentage": "Average Percentage Score (%)"
            })
            rankings["Overall Correct Ratio"] = rankings.apply(lambda r: f"{r['score']}/{r['total_questions']}", axis=1)
            rankings = rankings.sort_values(by="Average Percentage Score (%)", ascending=False).reset_index(drop=True)
            rankings.index = rankings.index + 1
            rankings = rankings[["Student Name", "Roll Number", "Average Percentage Score (%)", "Overall Correct Ratio"]]
            st.table(rankings.head(10))
    else:
        st.info("Analytics charts and leaderboards will populate once students submit exams.")

def admin_students_view():
    db = Database.get_client()
    st.markdown("## Student Management")
    
    tab_list, tab_add = st.tabs(["👥 Student List", "➕ Register New Student"])
    
    students = db.get_all_students()
    
    with tab_list:
        if not students:
            st.info("No students registered yet.")
        else:
            stud_df = pd.DataFrame([
                {
                    "Name": s["name"],
                    "Email": s["email"],
                    "Roll Number": s["roll_number"],
                    "Phone": s["phone"] or "N/A",
                    "Enrolled On": str(s["created_at"])[:10] if s.get("created_at") else "N/A",
                    "id": s["id"]
                } for s in students
            ])
            
            # Action: Edit/Delete
            st.dataframe(stud_df.drop(columns=["id"]))
            
            st.markdown("### Manage / Delete Student")
            target_roll = st.selectbox("Select Student Roll Number to Delete", options=[""] + [s["roll_number"] for s in students])
            if target_roll:
                target_stud = next(s for s in students if s["roll_number"] == target_roll)
                st.warning(f"Are you sure you want to permanently delete student **{target_stud['name']}** ({target_roll})?")
                if st.button("🗑️ Confirm Student Deletion", type="primary"):
                    success = db.delete_student(target_stud["id"])
                    # If SQLite fallback mode, also delete from local_auth
                    if db.mode == "Local (SQLite)":
                        try:
                            conn = db._get_connection()
                            conn.execute("DELETE FROM local_auth WHERE id = ?", (target_stud["id"],))
                            conn.commit()
                            conn.close()
                        except:
                            pass
                    if success:
                        st.success("Student records deleted successfully.")
                        st.rerun()
                    else:
                        st.error("Deletion failed.")
                        
    with tab_add:
        st.markdown("### Enroll Student Account")
        add_name = st.text_input("Student Full Name")
        add_email = st.text_input("Email Address")
        add_roll = st.text_input("Enrollment Number")
        add_phone = st.text_input("Phone Number")
        add_password = st.text_input("Password (Initial)", type="password")
        
        if st.button("Add Student", type="primary"):
            success, msg = Auth.signup_student(
                email=add_email,
                password=add_password,
                name=add_name,
                roll_number=add_roll,
                phone=add_phone
            )
            if success:
                st.success("Student successfully enrolled!")
                st.rerun()
            else:
                st.error(msg)

def admin_questions_view():
    db = Database.get_client()
    st.markdown("## Question Bank Management")
    
    tab_list, tab_add, tab_bulk = st.tabs([
        "📚 View Question Bank", 
        "✏️ Manual Question Creator", 
        "📤 Bulk Excel/CSV Upload"
    ])
    
    all_qs = db.get_all_questions()
    
    with tab_list:
        if not all_qs:
            st.info("The question bank is empty.")
        else:
            # Filter by topic
            topics_list = list(set([q["topic"] for q in all_qs]))
            selected_topic = st.selectbox("Filter by Topic", options=["All Topics"] + topics_list)
            
            filtered_qs = all_qs if selected_topic == "All Topics" else [q for q in all_qs if q["topic"] == selected_topic]
            
            st.markdown(f"**Showing {len(filtered_qs)} questions**")
            for idx, q in enumerate(filtered_qs):
                st.markdown(f"""
                <div class='premium-card'>
                    <div style='display:flex; justify-content:space-between; margin-bottom:5px;'>
                        <span style='font-weight:bold; color:#4F46E5;'>Q{idx+1}. Topic: {q['topic']}</span>
                        <div>
                            <span class='badge badge-info'>{q['difficulty']}</span>
                            <span class='badge' style='background-color:#E2E8F0; color:#475569;'>Type: {q['question_type']}</span>
                        </div>
                    </div>
                    <p style='font-size:1.05rem; font-weight:600;'>{q['question_text']}</p>
                    {f"<div style='font-size:0.9rem; color:#475569; padding-left:15px; margin-bottom:10px;'>A) {q['option_a']}<br/>B) {q['option_b']}<br/>C) {q['option_c']}<br/>D) {q['option_d']}</div>" if q['question_type'] == 'MCQ' else ""}
                    <div style='border-top:1px solid #F1F5F9; padding-top:5px; font-weight:bold; font-size:0.9rem; color:#166534;'>
                        Correct Option: {q['correct_option']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Delete Action
                if st.button(f"🗑️ Delete Q-{q['id']}", key=f"del_q_{q['id']}"):
                    if db.delete_question(q['id']):
                        st.success("Question deleted.")
                        st.rerun()
                    else:
                        st.error("Failed to delete question.")
                        
    with tab_add:
        st.markdown("### Create New Question")
        q_topic = st.text_input("Topic Category", placeholder="e.g. Computer Fundamentals")
        q_text = st.text_area("Question Text")
        q_type = st.radio("Question Type", options=["MCQ", "TF"], format_func=lambda x: "Multiple Choice Question (MCQ)" if x == "MCQ" else "True / False (TF)")
        
        q_a = q_b = q_c = q_d = ""
        if q_type == "MCQ":
            col_o1, col_o2 = st.columns(2)
            with col_o1:
                q_a = st.text_input("Option A")
                q_c = st.text_input("Option C")
            with col_o2:
                q_b = st.text_input("Option B")
                q_d = st.text_input("Option D")
            correct_opt = st.selectbox("Correct Option", options=["A", "B", "C", "D"])
        else:
            q_a = "True"
            q_b = "False"
            correct_opt = st.selectbox("Correct Option", options=["A", "B"], format_func=lambda x: "Option A (True)" if x == "A" else "Option B (False)")
            
        q_diff = st.selectbox("Difficulty Level", options=["Easy", "Medium", "Hard"])
        
        if st.button("Add Question to Bank", type="primary"):
            if not q_topic or not q_text or (q_type == "MCQ" and not (q_a and q_b and q_c and q_d)):
                st.error("Please fill in all question fields.")
            else:
                new_q = db.add_question(
                    topic=q_topic,
                    question_text=q_text,
                    question_type=q_type,
                    option_a=q_a,
                    option_b=q_b,
                    option_c=q_c,
                    option_d=q_d,
                    correct_option=correct_opt,
                    difficulty=q_diff
                )
                if new_q:
                    st.success("Question successfully added to question bank!")
                    st.rerun()
                else:
                    st.error("Failed to insert question.")
                    
    with tab_bulk:
        st.markdown("### Bulk Question Import")
        st.write("Upload an Excel or CSV file containing multiple questions.")
        
        st.markdown("""
        **Required File Schema / Columns:**
        `topic`, `question_text`, `question_type` (MCQ or TF), `option_a`, `option_b`, `option_c`, `option_d`, `correct_option` (A, B, C, or D), `difficulty` (Easy, Medium, Hard).
        
        *Note: For True/False (TF) questions, option_c and option_d can be left empty.*
        """)
        
        # Download Template CSV
        template_csv = "topic,question_text,question_type,option_a,option_b,option_c,option_d,correct_option,difficulty\n" \
                       "Computer Fundamentals,A printer is an input device.,TF,True,False,,,B,Easy\n" \
                       "Computer Fundamentals,What is the brain of the computer?,MCQ,RAM,CPU,HDD,ROM,B,Easy"
                       
        st.download_button(
            label="📥 Download Template CSV",
            data=template_csv,
            file_name="question_bulk_template.csv",
            mime="text/csv"
        )
        
        uploaded_file = st.file_uploader("Upload Excel or CSV template file", type=["csv", "xlsx"])
        if uploaded_file:
            try:
                if uploaded_file.name.endswith(".csv"):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                    
                st.write("Preview of Uploaded Data:")
                st.dataframe(df.head())
                
                # Check columns
                required_cols = {'topic', 'question_text', 'question_type', 'correct_option', 'difficulty'}
                if not required_cols.issubset(df.columns):
                    st.error(f"Missing required columns. File must contain at least: {required_cols}")
                else:
                    if st.button("Confirm Bulk Upload", type="primary"):
                        # Ensure fields are strings/clean
                        df['topic'] = df['topic'].astype(str).str.strip()
                        df['question_text'] = df['question_text'].astype(str).str.strip()
                        df['question_type'] = df['question_type'].astype(str).str.strip().str.upper()
                        df['correct_option'] = df['correct_option'].astype(str).str.strip().str.upper()
                        df['difficulty'] = df['difficulty'].astype(str).str.strip()
                        
                        # Replace nulls in options
                        for col in ['option_a', 'option_b', 'option_c', 'option_d']:
                            if col in df.columns:
                                df[col] = df[col].fillna("").astype(str)
                            else:
                                df[col] = ""
                                
                        count = db.bulk_upload_questions(df)
                        st.success(f"Successfully uploaded {count} questions to the bank!")
                        st.rerun()
            except Exception as e:
                st.error(f"Error parsing file: {e}")

def admin_exams_view():
    db = Database.get_client()
    st.markdown("## Examination Management")
    
    tab_list, tab_create = st.tabs(["📝 View Exams", "➕ Create New Exam"])
    
    exams = db.get_all_exams()
    all_qs = db.get_all_questions()
    
    with tab_list:
        if not exams:
            st.info("No examinations created yet.")
        else:
            for exam in exams:
                status_badge = "<span class='badge badge-pass'>ACTIVE</span>" if exam["is_active"] else "<span class='badge badge-fail'>INACTIVE</span>"
                desc = exam['description'] or "No description provided."
                st.markdown(f"""
                <div class='premium-card'>
                    <div style='display:flex; justify-content:space-between;'>
                        <h4 style='margin:0; color:#1E3A8A;'>{exam['title']}</h4>
                        {status_badge}
                    </div>
                    <p style='margin: 0.5rem 0; color:#475569;'>{desc}</p>
                    <div style='display:flex; gap:2rem; font-size:0.9rem; color:#64748B;'>
                        <span>⏱️ <b>Duration:</b> {exam['duration_minutes']} minutes</span>
                        <span>❓ <b>Questions Assigned:</b> {exam['total_questions']} items</span>
                        <span>🎯 <b>Passing Target:</b> {exam['passing_percentage']}%</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Delete Exam Action
                if st.button(f"🗑️ Delete Exam - {exam['title']}", key=f"del_ex_{exam['id']}"):
                    if db.delete_exam(exam['id']):
                        st.success("Exam deleted successfully.")
                        st.rerun()
                    else:
                        st.error("Failed to delete exam.")
                        
    with tab_create:
        if not all_qs:
            st.warning("Please add questions to the question bank before building an exam.")
            return
            
        st.markdown("### Create Examination Structure")
        ex_title = st.text_input("Exam Title", placeholder="e.g. Operating System Quick Quiz")
        ex_desc = st.text_area("Description")
        ex_duration = st.number_input("Duration (Minutes)", min_value=5, max_value=180, value=30)
        ex_passing = st.number_input("Passing Percentage Target", min_value=10.0, max_value=100.0, value=40.0, step=5.0)
        
        # Select questions from database
        st.markdown("#### Select Questions for the Exam Pool")
        st.write("Choose the set of questions from which this exam will pull.")
        
        # Organize questions in a list for multi-select
        q_options = []
        for q in all_qs:
            q_options.append({
                "id": q["id"],
                "display": f"[{q['topic']} | {q['difficulty']}] - {q['question_text'][:80]}..."
            })
            
        selected_q_display_vals = st.multiselect(
            "Select Questions",
            options=[o["display"] for o in q_options],
            help="Select the exact questions you wish to include in this exam."
        )
        
        # Filter matching ids
        selected_q_ids = []
        for d in selected_q_display_vals:
            match = next(o for o in q_options if o["display"] == d)
            selected_q_ids.append(match["id"])
            
        ex_count = st.number_input(
            "Questions Count per Attempt", 
            min_value=1, 
            max_value=max(1, len(selected_q_ids)), 
            value=min(10, max(1, len(selected_q_ids))),
            help="Number of questions randomly selected from the chosen pool for each student attempt."
        )
        
        ex_active = st.checkbox("Set Exam Active Immediately", value=True)
        
        if st.button("Publish Exam", type="primary"):
            if not ex_title or not selected_q_ids:
                st.error("Please fill in the Exam Title and select at least one question.")
            elif ex_count > len(selected_q_ids):
                st.error("Question count per attempt cannot exceed the size of the selected question pool.")
            else:
                exam = db.create_exam(
                    title=ex_title,
                    description=ex_desc,
                    duration_minutes=ex_duration,
                    total_questions=ex_count,
                    passing_percentage=ex_passing,
                    is_active=ex_active,
                    question_ids=selected_q_ids
                )
                if exam:
                    st.success(f"Exam '{ex_title}' published successfully!")
                    st.rerun()
                else:
                    st.error("Failed to build exam.")

def admin_reports_view():
    db = Database.get_client()
    st.markdown("## Exam Results & Performance Reports")
    
    results = db.get_all_results()
    if not results:
        st.info("No exam reports registered yet.")
        return
        
    res_df = pd.DataFrame([
        {
            "Student Name": r["students"]["name"],
            "Roll Number": r["students"]["roll_number"],
            "Exam Title": r["exams"]["title"],
            "Score": f"{r['score']}/{r['total_questions']}",
            "Percentage": f"{r['percentage']:.2f}%",
            "Grade": r["grade"],
            "Result": "PASSED" if r["passed"] else "FAILED",
            "Submitted On": str(r["submitted_at"])[:16],
            "id": r["id"]
        } for r in results
    ])
    
    # Download Report Button
    csv_buf = io.StringIO()
    res_df.drop(columns=["id"]).to_csv(csv_buf, index=False)
    st.download_button(
        label="📥 Download Performance Report (CSV)",
        data=csv_buf.getvalue(),
        file_name="BCC_Student_Exam_Report.csv",
        mime="text/csv"
    )
    
    # Reports list
    st.dataframe(res_df.drop(columns=["id"]))
    
    st.markdown("### View Detailed Candidate Sheet")
    selected_result_idx = st.selectbox(
        "Select Candidate Submission", 
        options=res_df.index, 
        format_func=lambda x: f"{res_df.loc[x, 'Student Name']} ({res_df.loc[x, 'Roll Number']}) - {res_df.loc[x, 'Exam Title']} [{res_df.loc[x, 'Result']}]"
    )
    
    if selected_result_idx is not None:
        # Cast to int to prevent psycopg2 numpy.int64 adaptation errors
        result_id = int(res_df.loc[selected_result_idx, "id"])
        result_details = db.get_result_by_id(result_id)
        responses = db.get_result_responses(result_id)
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            student_info = result_details.get("students") or {}
            st.markdown(f"""
            <div class='premium-card'>
                <h4 style='margin-top:0; color:#1E3A8A;'>Candidate Details</h4>
                <b>Name:</b> {student_info.get('name', 'Unknown')}<br/>
                <b>Roll Number:</b> {student_info.get('roll_number', 'Unknown')}<br/>
                <b>Email:</b> {student_info.get('email', 'Unknown')}<br/>
                <b>Phone:</b> {student_info.get('phone') or 'N/A'}<br/>
            </div>
            """, unsafe_allow_html=True)
        with col_m2:
            exam_info = result_details.get("exams") or {}
            st.markdown(f"""
            <div class='premium-card'>
                <h4 style='margin-top:0; color:#1E3A8A;'>Performance Summary</h4>
                <b>Exam Taken:</b> {exam_info.get('title', 'Unknown')}<br/>
                <b>Grade Awarded:</b> {result_details.get('grade', 'N/A')}<br/>
                <b>Correct Ratio:</b> {result_details.get('score', 0)} / {result_details.get('total_questions', 0)}<br/>
                <b>Percentage Score:</b> {result_details.get('percentage', 0):.2f}%<br/>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("#### Detailed Student Response Log")
        for idx, resp in enumerate(responses):
            q_info = resp["question_bank"]
            is_correct = resp["is_correct"]
            indicator_color = "#10B981" if is_correct else "#EF4444"
            indicator_text = "CORRECT" if is_correct else "INCORRECT"
            
            st.markdown(f"""
            <div style='background-color:#F8FAFC; border-left:4px solid {indicator_color}; border-radius:4px; padding:12px; margin-bottom:12px;'>
                <div style='display:flex; justify-content:space-between; font-size:0.85rem; font-weight:bold; color:#64748B;'>
                    <span>QUESTION {idx+1} ({q_info['difficulty']})</span>
                    <span style='color:{indicator_color};'>{indicator_text}</span>
                </div>
                <p style='margin:5px 0; font-weight:600; color:#1E293B;'>{q_info['question_text']}</p>
                <div style='font-size:0.9rem; color:#475569;'>
                    Selected Option: <b>{resp['selected_option']}</b> | Correct Option: <b>{q_info['correct_option']}</b>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ====================================================================
# EXAM RESULT SCREEN & ROUTING ROOT
# ====================================================================
if __name__ == "__main__":
    # Handle global verification URLs if present
    query_params = st.query_params
    if "verify" in query_params:
        UIHelper.inject_custom_css()
        
        cert_id = query_params["verify"]
        db = Database.get_client()
        cert_details = db.get_certificate_by_id(cert_id)
        
        st.markdown("<div style='margin-top:2rem;'></div>", unsafe_allow_html=True)
        UIHelper.render_header(Config.INSTITUTE_NAME, "Secure Certificate Verification Portal")
        
        if cert_details:
            st.markdown(f"""
            <div style='background-color:#DCFCE7; border: 2px solid #10B981; border-radius:12px; padding:25px; text-align:center;'>
                <div style='font-size:3rem; margin-bottom:10px;'>✅</div>
                <h2 style='color:#166534; margin:0;'>VERIFIED CREDENTIAL</h2>
                <p style='color:#166534; font-size:1.1rem; margin-top:5px;'>
                    Certificate ID: <b>{cert_id}</b>
                </p>
                <hr style='border:0; border-top:1px solid #BBF7D0; margin:15px 0;'/>
                <table style='width:100%; border-collapse:collapse; text-align:left; color:#1E293B;'>
                    <tr><td style='padding:6px; font-weight:bold; color:#1E3A8A;'>Recipient Student:</td><td>{cert_details['students']['name']}</td></tr>
                    <tr><td style='padding:6px; font-weight:bold; color:#1E3A8A;'>Roll Number:</td><td>{cert_details['students']['roll_number']}</td></tr>
                    <tr><td style='padding:6px; font-weight:bold; color:#1E3A8A;'>Exam Completed:</td><td>{cert_details['results']['exams']['title']}</td></tr>
                    <tr><td style='padding:6px; font-weight:bold; color:#1E3A8A;'>Grade Achieved:</td><td><b>{cert_details['results']['grade']}</b> ({cert_details['results']['percentage']:.2f}%)</td></tr>
                    <tr><td style='padding:6px; font-weight:bold; color:#1E3A8A;'>Date of Issue:</td><td>{str(cert_details['issue_date'])[:10]}</td></tr>
                </table>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style='background-color:#FEE2E2; border: 2px solid #EF4444; border-radius:12px; padding:25px; text-align:center;'>
                <div style='font-size:3rem; margin-bottom:10px;'>❌</div>
                <h2 style='color:#991B1B; margin:0;'>INVALID CREDENTIAL</h2>
                <p style='color:#991B1B; font-size:1.1rem; margin-top:5px;'>
                    The Certificate ID <b>{cert_id}</b> could not be verified in our registry records.
                </p>
                <p style='color:#475569; font-size:0.95rem;'>
                    Please verify that the URL is exact and has not been modified.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
        if st.button("⬅️ Go to Portal Homepage", use_container_width=True):
            st.query_params.clear()
            st.rerun()
    elif st.session_state.get("current_view") == "ExamResultScreen":
        # Render custom full page for results display
        UIHelper.inject_custom_css()
        show_exam_results_screen()
    else:
        main()
