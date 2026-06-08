# Basic Computer Course (BCC) Examination Portal

A production-ready, beautiful, and secure Streamlit web application designed for conducting the **Basic Computer Course (BCC)** examinations, featuring interactive dashboards, randomized question selections, auto-evaluation, analytics charts, and dynamic PDF certificate generation with secure verification QR codes.

---

## 🛠️ Technology Stack
- **Core Engine:** Python 3.12, Streamlit
- **Database:** Supabase PostgreSQL (Cloud) / Local SQLite (Sandbox Fallback)
- **Security:** Supabase Authentication / Local Hashed passwords (bcrypt)
- **Reporting:** ReportLab (PDF Certificates)
- **Analytics:** Pandas & Plotly (Visualizations)

---

## 📁 Folder Structure
```
BCC_Exam_Portal/
│
├── .streamlit/
│   └── config.toml          # Custom theme configuration (indigo/slate aesthetics)
│
├── database/
│   ├── schema.sql           # Database setup script (tables, triggers, RLS policies)
│   └── seed_data.sql        # Initial question bank and mock data
│
├── src/
│   ├── __init__.py
│   ├── config.py            # Environment variable loader and settings management
│   ├── database.py          # Dual-mode database interface (Supabase + SQLite fallback)
│   ├── auth.py              # User authentication & session management (Supabase Auth + bcrypt)
│   ├── certificate.py       # PDF certificate builder using ReportLab with embedded QR Code
│   ├── evaluation.py        # Automated grading, topic-wise analysis, and ranking logic
│   └── utils.py             # UI helpers, branding, charts, custom CSS styling
│
├── app.py                   # Streamlit main entry point and page router
├── requirements.txt         # Package dependencies
├── .env.example             # Template for API keys and connection parameters
└── README.md                # Detailed setup and documentation (this file)
```

---

## 🚀 Setup & Installation

### 1. Clone or Copy the Repository
Place the application files in your local directory (e.g. `c:/Users/Admin/Documents/BCC_Exam_Portal`).

### 2. Install Dependencies
Run the following command in your terminal to install all required libraries:
```bash
pip install -r requirements.txt
```

### 3. Run Locally (Sandbox Mode)
If you do not have a Supabase project set up yet, the application will automatically fall back to **Local SQLite Mode**. It will create a database file `bcc_portal.db` in your root folder, seed it with sample questions, and create a default administrator account.

Start the Streamlit application:
```bash
streamlit run app.py
```

#### 🔑 Local Admin Login Credentials:
- **Email:** `admin@bcc.com`
- **Password:** `admin123`

*Note: You can register student accounts directly via the **Student Registration** tab on the login screen.*

---

## 🌐 Supabase Production Configuration

To configure the application to run with your live **Supabase** cloud database and authentication service:

### 1. Execute SQL Schema
1. Log in to your [Supabase Dashboard](https://supabase.com).
2. Open your project, click on the **SQL Editor** on the left menu.
3. Click **New Query**, copy the entire contents of [schema.sql](file:///c:/Users/Admin/Documents/BCC_Exam_Portal/database/schema.sql), and click **Run**.
4. *(Optional)* Create another query, copy [seed_data.sql](file:///c:/Users/Admin/Documents/BCC_Exam_Portal/database/seed_data.sql), and run it to pre-populate exams and question bank.

### 2. Setup Environment Variables
Create a file named `.env` in the root folder of the project (copying `.env.example`) and fill in your Supabase project parameters:
```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-anon-key-or-service-key
SESSION_TIMEOUT_MINUTES=30
```
Alternatively, if deploying directly to Streamlit Community Cloud, navigate to **Settings -> Secrets** on your Streamlit Dashboard and paste:
```toml
SUPABASE_URL = "https://your-project-id.supabase.co"
SUPABASE_KEY = "your-supabase-anon-key-or-service-key"
```

Once configured, the app will dynamically connect to your Supabase project on startup!

---

## 🔒 Security & Row Level Security (RLS)
The database has Row Level Security (RLS) configured to isolate data access:
1. **Admins:** Have read/write access to all tables (`admins`, `students`, `question_bank`, `exams`, `results`, `responses`, `certificates`).
2. **Students:** 
   - Can only read their own profile row in the `students` table.
   - Can read questions from the question bank during active exams.
   - Can view the list of active exams.
   - Can create and view only their own results, answers, and certificates.
   
Password hashing is handled natively by Supabase Authentication in cloud mode, and securely hashed with salt rounds using `bcrypt` in local fallback sandbox mode.

---

## 📜 Certificate Verification QR System
When a student passes an exam:
1. A unique certificate ID is generated (format: `BCC-YYYYMMDD-RESULT_ID`).
2. A PDF certificate is compiled programmatically in-memory using `ReportLab`.
3. A verification QR Code is embedded in the PDF footer.
4. Scanning the QR Code redirects to the portal's verification URL (e.g. `https://your-portal.streamlit.app/?verify=BCC-YYYYMMDD-RESULT_ID`).
5. The portal checks the database registry and displays a verified credential details sheet (Student name, Roll number, Course name, Grade, Score, and Issue date) to ensure the certificate is authentic.
