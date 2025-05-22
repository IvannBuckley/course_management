-- 1. First create the database
CREATE DATABASE IF NOT EXISTS course_management_system;
USE course_management_system;

-- Users table 
CREATE TABLE Users (
    acc_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,  
    user_type ENUM('student', 'lecturer', 'admin') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Students table 
CREATE TABLE Students (
    st_id INT AUTO_INCREMENT PRIMARY KEY,
    acc_id INT UNIQUE NOT NULL,
    FOREIGN KEY (acc_id) REFERENCES Users(acc_id) ON DELETE CASCADE
);

-- Lecturers table
CREATE TABLE Lecturers (
    l_id INT AUTO_INCREMENT PRIMARY KEY,
    acc_id INT UNIQUE NOT NULL,
    FOREIGN KEY (acc_id) REFERENCES Users(acc_id) ON DELETE CASCADE
);

-- Admins table 
CREATE TABLE Admins (
    admin_id INT AUTO_INCREMENT PRIMARY KEY,
    acc_id INT UNIQUE NOT NULL,
    FOREIGN KEY (acc_id) REFERENCES Users(acc_id) ON DELETE CASCADE
);

-- Courses table 
CREATE TABLE Courses (
    crs_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    crs_des TEXT,
    lecturer_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lecturer_id) REFERENCES Lecturers(l_id) ON DELETE RESTRICT
);

-- Student_Course junction table
CREATE TABLE Student_Course (
    st_id INT NOT NULL,
    crs_id INT NOT NULL,
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (st_id, crs_id),
    FOREIGN KEY (st_id) REFERENCES Students(st_id) ON DELETE CASCADE,
    FOREIGN KEY (crs_id) REFERENCES Courses(crs_id) ON DELETE CASCADE
);

-- Calendar events
CREATE TABLE Calendar (
    cal_id INT AUTO_INCREMENT PRIMARY KEY,
    crs_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    event_date DATE NOT NULL,
    start_time TIME,
    end_time TIME,
    created_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (crs_id) REFERENCES Courses(crs_id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES Users(acc_id) ON DELETE CASCADE
);

-- Assignments
CREATE TABLE Assignments (
    assign_id INT AUTO_INCREMENT PRIMARY KEY,
    crs_id INT NOT NULL,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    due_date DATETIME NOT NULL,
    max_score DECIMAL(5,2) NOT NULL,
    created_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (crs_id) REFERENCES Courses(crs_id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES Users(acc_id) ON DELETE CASCADE
);

-- Submissions 
CREATE TABLE Submissions (
    submission_id INT AUTO_INCREMENT PRIMARY KEY,
    assign_id INT NOT NULL,
    st_id INT NOT NULL,
    submission_text TEXT,
    file_path VARCHAR(255),
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assign_id) REFERENCES Assignments(assign_id) ON DELETE CASCADE,
    FOREIGN KEY (st_id) REFERENCES Students(st_id) ON DELETE CASCADE
);

-- Grades 
CREATE TABLE Grades (
    grade_id INT AUTO_INCREMENT PRIMARY KEY,
    submission_id INT NOT NULL UNIQUE,
    score DECIMAL(5,2) NOT NULL,
    feedback TEXT,
    graded_by INT NOT NULL,
    graded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (submission_id) REFERENCES Submissions(submission_id) ON DELETE CASCADE,
    FOREIGN KEY (graded_by) REFERENCES Users(acc_id) ON DELETE CASCADE
);

-- Forums 
CREATE TABLE Forums (
    for_id INT AUTO_INCREMENT PRIMARY KEY,
    crs_id INT NOT NULL,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    created_by INT NOT NULL,
    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (crs_id) REFERENCES Courses(crs_id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES Users(acc_id) ON DELETE CASCADE
);

-- Threads 
CREATE TABLE Threads (
    t_id INT AUTO_INCREMENT PRIMARY KEY,
    for_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    created_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (for_id) REFERENCES Forums(for_id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES Users(acc_id) ON DELETE CASCADE
);

-- Thread_Replies 
CREATE TABLE Thread_Replies (
    reply_id INT AUTO_INCREMENT PRIMARY KEY,
    t_id INT NOT NULL,
    parent_reply_id INT NULL,
    user_id INT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (t_id) REFERENCES Threads(t_id) ON DELETE CASCADE,
    FOREIGN KEY (parent_reply_id) REFERENCES Thread_Replies(reply_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES Users(acc_id) ON DELETE CASCADE
);

-- Sections 
CREATE TABLE Sections (
    sec_id INT AUTO_INCREMENT PRIMARY KEY,
    crs_id INT NOT NULL,
    sec_num INT NOT NULL,
    title VARCHAR(100) NOT NULL,
    FOREIGN KEY (crs_id) REFERENCES Courses(crs_id) ON DELETE CASCADE
);

-- Section_Items
CREATE TABLE Section_Items (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    sec_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    item_type ENUM('slides', 'file', 'link') NOT NULL,
    content_url TEXT,
    file_path VARCHAR(255),
    created_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sec_id) REFERENCES Sections(sec_id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES Users(acc_id) ON DELETE CASCADE
);

-- All courses with 50+ students
CREATE VIEW courses_with_50_or_more_students AS
SELECT c.crs_id, c.name, COUNT(sc.st_id) AS student_count
FROM Courses c
JOIN Student_Course sc ON c.crs_id = sc.crs_id
GROUP BY c.crs_id, c.name
HAVING COUNT(sc.st_id) >= 50;

-- Students taking 5+ courses
CREATE VIEW students_with_5_or_more_courses AS
SELECT u.acc_id, u.name, COUNT(sc.crs_id) AS course_count
FROM Users u
JOIN Students s ON u.acc_id = s.acc_id
JOIN Student_Course sc ON s.st_id = sc.st_id
WHERE u.user_type = 'student'
GROUP BY u.acc_id, u.name
HAVING COUNT(sc.crs_id) >= 5;

-- Lecturers teaching 3+ courses
CREATE VIEW lecturers_with_3_or_more_courses AS
SELECT u.acc_id, u.name, COUNT(c.crs_id) AS course_count
FROM Users u
JOIN Lecturers l ON u.acc_id = l.acc_id
JOIN Courses c ON l.l_id = c.lecturer_id
WHERE u.user_type = 'lecturer'
GROUP BY u.acc_id, u.name
HAVING COUNT(c.crs_id) >= 3;

-- Top 10 most enrolled courses
CREATE VIEW top_10_most_enrolled_courses AS
SELECT c.crs_id, c.name, COUNT(sc.st_id) AS enrollment_count
FROM Courses c
JOIN Student_Course sc ON c.crs_id = sc.crs_id
GROUP BY c.crs_id, c.name
ORDER BY enrollment_count DESC
LIMIT 10;

-- Top 10 students by average grade
CREATE VIEW top_10_students_by_average AS
SELECT u.acc_id, u.name, AVG(g.score) AS average_score
FROM Users u
JOIN Students s ON u.acc_id = s.acc_id
JOIN Submissions sub ON s.st_id = sub.st_id
JOIN Grades g ON sub.submission_id = g.submission_id
WHERE u.user_type = 'student'
GROUP BY u.acc_id, u.name
ORDER BY average_score DESC
LIMIT 10;








