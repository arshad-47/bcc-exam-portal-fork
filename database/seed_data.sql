-- Seed Questions for Basic Computer Course Exam Portal

-- ====================================================================
-- SEED QUESTIONS FOR QUESTION BANK
-- ====================================================================
INSERT INTO question_bank (topic, question_text, question_type, option_a, option_b, option_c, option_d, correct_option, difficulty) VALUES
-- Computer Fundamentals (MCQs)
('Computer Fundamentals', 'Which of the following is considered the brain of the computer?', 'MCQ', 'Random Access Memory (RAM)', 'Central Processing Unit (CPU)', 'Hard Disk Drive (HDD)', 'Read Only Memory (ROM)', 'B', 'Easy'),
('Computer Fundamentals', 'What is the full form of ALU in computer architecture?', 'MCQ', 'Arithmetic Logic Unit', 'Advanced Logical Utility', 'Algorithm Learning Unit', 'Alternative Local Utility', 'A', 'Easy'),
('Computer Fundamentals', 'Which type of computer memory is volatile?', 'MCQ', 'ROM', 'Flash Memory', 'RAM', 'EPROM', 'C', 'Medium'),
('Computer Fundamentals', '1 Terabyte (TB) is equal to how many Gigabytes (GB)?', 'MCQ', '1000 GB', '1024 GB', '10000 GB', '512 GB', 'B', 'Easy'),
('Computer Fundamentals', 'Which of the following is an input device?', 'MCQ', 'Monitor', 'Printer', 'Scanner', 'Speaker', 'C', 'Easy'),

-- Operating Systems (MCQs)
('Operating Systems', 'Which of the following is NOT an operating system?', 'MCQ', 'Linux', 'Windows 11', 'Oracle Database', 'macOS Sonoma', 'C', 'Easy'),
('Operating Systems', 'What is the shortcut key to permanently delete a file or folder in Windows without sending it to the Recycle Bin?', 'MCQ', 'Delete', 'Shift + Delete', 'Ctrl + Delete', 'Alt + Delete', 'B', 'Easy'),
('Operating Systems', 'Which operating system component manages the system resources and communicates directly with hardware?', 'MCQ', 'Shell', 'Kernel', 'GUI', 'Registry', 'B', 'Medium'),
('Operating Systems', 'What is the utility program in Windows used to clean up unnecessary files?', 'MCQ', 'Disk Cleanup', 'Task Manager', 'Control Panel', 'Device Manager', 'A', 'Easy'),

-- MS Word (MCQs)
('MS Word', 'Which shortcut is used to align text to the center in MS Word?', 'MCQ', 'Ctrl + C', 'Ctrl + E', 'Ctrl + J', 'Ctrl + R', 'B', 'Easy'),
('MS Word', 'What is the default extension of a file saved in MS Word 2016?', 'MCQ', '.txt', '.doc', '.docx', '.pdf', 'C', 'Easy'),
('MS Word', 'Which tool is used in MS Word to copy formatting from one place and apply it to another?', 'MCQ', 'Format Painter', 'Copy-Paste', 'Cloner', 'Style Brush', 'A', 'Easy'),
('MS Word', 'Mail Merge is a feature found in which of the following tabs?', 'MCQ', 'Home', 'Insert', 'Mailings', 'Review', 'C', 'Easy'),

-- MS Excel (MCQs)
('MS Excel', 'Which formula correctly adds cells A1, A2, and A3 in MS Excel?', 'MCQ', '=ADD(A1:A3)', '=SUM(A1:A3)', '=TOTAL(A1:A3)', '=A1+A3', 'B', 'Easy'),
('MS Excel', 'What is the intersection of a row and a column in MS Excel called?', 'MCQ', 'Grid', 'Box', 'Cell', 'Workspace', 'C', 'Easy'),
('MS Excel', 'Which Excel function is used to count the number of cells that contain numbers in a range?', 'MCQ', 'COUNTA', 'COUNT', 'COUNTIF', 'SUM', 'B', 'Medium'),
('MS Excel', 'By default, text values in an Excel cell are aligned to the:', 'MCQ', 'Left', 'Right', 'Center', 'Justify', 'A', 'Easy'),

-- Internet & Web (MCQs)
('Internet & Web', 'What does DNS stand for in networking?', 'MCQ', 'Domain Name System', 'Dynamic Network Service', 'Digital Name Server', 'Data Network Schema', 'A', 'Medium'),
('Internet & Web', 'Which protocol is used to secure communications over the computer network by encrypting web traffic?', 'MCQ', 'HTTP', 'FTP', 'HTTPS', 'SMTP', 'C', 'Easy'),
('Internet & Web', 'Which of the following is a search engine?', 'MCQ', 'Google Chrome', 'Mozilla Firefox', 'DuckDuckGo', 'Safari', 'C', 'Easy'),

-- True / False Questions
('Computer Fundamentals', 'A scanner is an output device.', 'TF', 'True', 'False', NULL, NULL, 'B', 'Easy'),
('Operating Systems', 'Linux is open-source software.', 'TF', 'True', 'False', NULL, NULL, 'A', 'Easy'),
('MS Word', 'The keyboard shortcut Ctrl+S is used to Save a document.', 'TF', 'True', 'False', NULL, NULL, 'A', 'Easy'),
('MS Excel', 'Every Excel formula must begin with an equals (=) sign.', 'TF', 'True', 'False', NULL, NULL, 'A', 'Easy'),
('Internet & Web', 'An IP address changes depending on the network you connect to.', 'TF', 'True', 'False', NULL, NULL, 'A', 'Medium'),
('Computer Fundamentals', 'ROM stands for Read Only Memory and is non-volatile.', 'TF', 'True', 'False', NULL, NULL, 'A', 'Easy');


-- ====================================================================
-- SEED EXAMS
-- ====================================================================
INSERT INTO exams (title, description, duration_minutes, total_questions, passing_percentage, is_active) VALUES
('Unified BCC Certification Exam', 'Comprehensive examination covering Computer Fundamentals, Windows OS, MS Word, MS Excel, MS PowerPoint, and Internet basics, alongside a typing test.', 30, 26, 40.0, TRUE);

-- ====================================================================
-- SEED EXAM QUESTIONS (Assign questions to the exams)
-- ====================================================================
-- For Unified Exam (Assign all questions, assuming IDs 1 to 26 exist based on the previous inserts + any additional seeds)
INSERT INTO exam_questions (exam_id, question_id) 
SELECT 1, id FROM question_bank;
