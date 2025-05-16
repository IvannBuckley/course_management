import random
from faker import Faker
import mysql.connector
from datetime import datetime, timedelta
import hashlib
import string
from tqdm import tqdm

# Initialize Faker
fake = Faker()

# Database connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Mufa$ac@t123",
    database="course_management_system",
    pool_size=10,
    connect_timeout=300
)
cursor = db.cursor()

# Constants based on requirements
NUM_STUDENTS = 1000 #using 1k student as test case

NUM_COURSES = 200
NUM_LECTURERS = 50  # 200 courses / 5 max per lecturer = minimum 40
MIN_COURSES_PER_STUDENT = 3
MAX_COURSES_PER_STUDENT = 6
MIN_STUDENTS_PER_COURSE = 10
MAX_LECTURER_COURSES = 5
MIN_LECTURER_COURSES = 1

# Additional constants for other features
FORUMS_PER_COURSE = (1, 3)  # Random range
THREADS_PER_FORUM = (5, 15)
REPLIES_PER_THREAD = (0, 10)
ASSIGNMENTS_PER_COURSE = (3, 8)
EVENTS_PER_COURSE = (5, 12)
SECTIONS_PER_COURSE = (4, 8)
ITEMS_PER_SECTION = (3, 7)

def hash_password(password):
    """Hash a password for storing using SHA-256 (for demo purposes)."""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_random_password(length=12):
    """Generate a random password with letters, digits, and special chars"""
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(chars) for _ in range(length))

def generate_users(user_type, count, start_index=0):
    """Generate guaranteed-unique users of a specific type"""
    users = []
    for i in range(start_index, start_index + count):
        name = fake.name()
        email = f"{user_type}{i}@example.com"  # Guarantees uniqueness
        password = hash_password(generate_random_password())
        users.append((name, email, password, user_type))
    return users

def insert_users(users):
    """Insert users into database"""
    sql = "INSERT INTO Users (name, email, password, user_type) VALUES (%s, %s, %s, %s)"
    cursor.executemany(sql, users)
    db.commit()
    return cursor.lastrowid - len(users) + 1  # Return first ID

def generate_courses(num_courses, lecturer_ids):
    """Generate courses with lecturer assignments"""
    courses = []
    lecturer_course_counts = {lid: 0 for lid in lecturer_ids}
    
    # Ensure each lecturer teaches at least 1 course
    for lecturer_id in lecturer_ids:
        course_name = f"{fake.word().capitalize()} {fake.word().capitalize()} {random.choice(['I', 'II', 'III', '101', '201', '301'])}"
        description = fake.text(max_nb_chars=200)
        courses.append((course_name, description, lecturer_id))
        lecturer_course_counts[lecturer_id] += 1
    
    # Distribute remaining courses
    for _ in range(num_courses - len(lecturer_ids)):
        # Get lecturers with less than max courses
        available_lecturers = [lid for lid, count in lecturer_course_counts.items() 
                             if count < MAX_LECTURER_COURSES]
        if not available_lecturers:
            raise ValueError("Not enough lecturers to distribute courses")
        
        lecturer_id = random.choice(available_lecturers)
        course_name = f"{fake.word().capitalize()} {fake.word().capitalize()} {random.choice(['I', 'II', 'III', '101', '201', '301'])}"
        description = fake.text(max_nb_chars=200)
        courses.append((course_name, description, lecturer_id))
        lecturer_course_counts[lecturer_id] += 1
    
    return courses

def insert_courses(courses):
    """Insert courses into database"""
    sql = "INSERT INTO Courses (name, crs_des, lecturer_id) VALUES (%s, %s, %s)"
    cursor.executemany(sql, courses)
    db.commit()
    return cursor.lastrowid - len(courses) + 1  # Return first ID

def enroll_students(course_ids, student_ids):
    """Enroll students in courses meeting all requirements"""
    enrollments = []
    
    # Track student course counts
    student_course_counts = {sid: 0 for sid in student_ids}
    
    # Track course student counts
    course_student_counts = {cid: 0 for cid in course_ids}
    
    # First ensure each student is in at least MIN courses
    for student_id in student_ids:
        needed = MIN_COURSES_PER_STUDENT
        available_courses = [cid for cid in course_ids 
                           if course_student_counts[cid] < NUM_STUDENTS and
                           (student_id, cid) not in enrollments]
        
        selected = random.sample(available_courses, min(needed, len(available_courses)))
        for course_id in selected:
            enrollments.append((student_id, course_id))
            student_course_counts[student_id] += 1
            course_student_counts[course_id] += 1
    
    # Then ensure each course has at least MIN students
    for course_id in course_ids:
        needed = max(0, MIN_STUDENTS_PER_COURSE - course_student_counts[course_id])
        if needed > 0:
            available_students = [sid for sid in student_ids 
                                if student_course_counts[sid] < MAX_COURSES_PER_STUDENT and
                                (sid, course_id) not in enrollments]
            
            selected = random.sample(available_students, min(needed, len(available_students)))
            for student_id in selected:
                enrollments.append((student_id, course_id))
                student_course_counts[student_id] += 1
                course_student_counts[course_id] += 1
    
    # Fill remaining enrollments randomly
    for student_id in student_ids:
        current = student_course_counts[student_id]
        if current < MAX_COURSES_PER_STUDENT:
            available_courses = [cid for cid in course_ids 
                               if course_student_counts[cid] < NUM_STUDENTS and
                               (student_id, cid) not in enrollments]
            
            max_additional = MAX_COURSES_PER_STUDENT - current
            additional = random.randint(0, min(max_additional, len(available_courses)))
            
            selected = random.sample(available_courses, additional) if available_courses else []
            for course_id in selected:
                enrollments.append((student_id, course_id))
                student_course_counts[student_id] += 1
                course_student_counts[course_id] += 1
    
    return enrollments

def insert_enrollments(enrollments):
    """Insert student-course enrollments"""
    sql = "INSERT INTO Student_Course (st_id, crs_id) VALUES (%s, %s)"
    cursor.executemany(sql, enrollments)
    db.commit()

def generate_forums(course_ids, lecturer_user_ids):
    """Generate forums for courses"""
    forums = []
    for course_id in course_ids:
        num_forums = random.randint(*FORUMS_PER_COURSE)
        for _ in range(num_forums):
            title = f"{fake.word().capitalize()} {fake.word().capitalize()} Forum"
            description = fake.sentence()
            created_by = random.choice(lecturer_user_ids)
            forums.append((course_id, title, description, created_by))
    return forums

def insert_forums(forums):
    """Insert forums into database"""
    sql = """INSERT INTO Forums (crs_id, title, description, created_by, date_created) 
             VALUES (%s, %s, %s, %s, NOW())"""
    cursor.executemany(sql, forums)
    db.commit()
    return cursor.lastrowid - len(forums) + 1  # Return first ID

def generate_threads(forums, student_user_ids, lecturer_user_ids):
    """Generate discussion threads for forums"""
    threads = []
    for forum in forums:
        forum_id = forum[0]
        num_threads = random.randint(*THREADS_PER_FORUM)
        for _ in range(num_threads):
            title = fake.sentence(nb_words=6)[:-1]  # Remove period
            content = fake.paragraph(nb_sentences=3)
            # Mix of students and lecturers creating threads
            created_by = random.choice(student_user_ids + lecturer_user_ids)
            threads.append((forum_id, title, content, created_by))
    return threads

def insert_threads(threads):
    """Insert threads into database"""
    sql = """INSERT INTO Threads (for_id, title, content, created_by, created_at) 
             VALUES (%s, %s, %s, %s, NOW())"""
    cursor.executemany(sql, threads)
    db.commit()
    return cursor.lastrowid - len(threads) + 1  # Return first ID

def generate_replies(threads, student_user_ids, lecturer_user_ids):
    """Generate replies to threads (including nested replies)"""
    replies = []
    for thread in threads:
        thread_id = thread[0]
        num_replies = random.randint(*REPLIES_PER_THREAD)
        
        # Generate top-level replies
        top_level_replies = []
        for _ in range(num_replies):
            content = fake.paragraph(nb_sentences=2)
            user_id = random.choice(student_user_ids + lecturer_user_ids)
            top_level_replies.append((thread_id, None, user_id, content))
        
        # Generate some nested replies
        nested_replies = []
        for reply in top_level_replies:
            if random.random() < 0.3:  # 30% chance of having nested replies
                num_nested = random.randint(1, 3)
                for _ in range(num_nested):
                    content = fake.paragraph(nb_sentences=2)
                    user_id = random.choice(student_user_ids + lecturer_user_ids)
                    nested_replies.append((thread_id, reply[0], user_id, content))
        
        replies.extend(top_level_replies)
        replies.extend(nested_replies)
    
    return replies

def insert_replies(replies):
    """Insert thread replies into database"""
    sql = """INSERT INTO Thread_Replies (t_id, parent_reply_id, user_id, content, created_at) 
             VALUES (%s, %s, %s, %s, NOW())"""
    cursor.executemany(sql, replies)
    db.commit()

def generate_assignments(course_ids, lecturer_user_ids):
    """Generate assignments for courses"""
    assignments = []
    for course_id in course_ids:
        num_assignments = random.randint(*ASSIGNMENTS_PER_COURSE)
        for i in range(num_assignments):
            title = f"Assignment {i+1}: {fake.word().capitalize()}"
            description = fake.paragraph(nb_sentences=2)
            due_date = fake.date_between(start_date='today', end_date='+3m')
            max_score = random.choice([10, 20, 30, 50, 100])
            created_by = random.choice(lecturer_user_ids)
            assignments.append((course_id, title, description, due_date, max_score, created_by))
    return assignments

def insert_assignments(assignments):
    """Insert assignments into database"""
    sql = """INSERT INTO Assignments (crs_id, title, description, due_date, max_score, created_by, created_at) 
             VALUES (%s, %s, %s, %s, %s, %s, NOW())"""
    cursor.executemany(sql, assignments)
    db.commit()
    return cursor.lastrowid - len(assignments) + 1  # Return first ID

def generate_submissions(assignments, student_ids):
    """Generate student submissions for assignments"""
    submissions = []
    grades = []
    
    for assignment in assignments:
        assignment_id = assignment[0]
        course_id = assignment[1]
        
        # Get students enrolled in this course
        cursor.execute("SELECT st_id FROM Student_Course WHERE crs_id = %s", (course_id,))
        enrolled_students = [row[0] for row in cursor.fetchall()]
        
        # Each student has a 70% chance of submitting
        for student_id in enrolled_students:
            if random.random() < 0.7:
                submission_text = fake.paragraph(nb_sentences=3)
                file_path = f"/uploads/assignment_{assignment_id}_student_{student_id}.pdf"
                submissions.append((assignment_id, student_id, submission_text, file_path))
                
                # 80% of submissions are graded
                if random.random() < 0.8:
                    score = round(random.uniform(50, 100), 2)
                    feedback = random.choice([
                        "Excellent work!",
                        "Good job, but could use more detail.",
                        "Needs improvement in several areas.",
                        "Well researched and presented.",
                        "Submitted late, but good quality."
                    ])
                    # Assume graded by course lecturer
                    cursor.execute("SELECT lecturer_id FROM Courses WHERE crs_id = %s", (course_id,))
                    lecturer_id = cursor.fetchone()[0]
                    cursor.execute("SELECT acc_id FROM Lecturers WHERE l_id = %s", (lecturer_id,))
                    graded_by = cursor.fetchone()[0]
                    
                    grades.append((len(submissions), score, feedback, graded_by))
    
    return submissions, grades

def insert_submissions(submissions):
    """Insert submissions into database"""
    sql = """INSERT INTO Submissions (assign_id, st_id, submission_text, file_path, submitted_at) 
             VALUES (%s, %s, %s, %s, NOW())"""
    cursor.executemany(sql, submissions)
    db.commit()
    return cursor.lastrowid - len(submissions) + 1  # Return first ID

def insert_grades(grades):
    """Insert grades into database"""
    sql = """INSERT INTO Grades (submission_id, score, feedback, graded_by, graded_at) 
             VALUES (%s, %s, %s, %s, NOW())"""
    cursor.executemany(sql, grades)
    db.commit()

def generate_events(course_ids, lecturer_user_ids):
    """Generate calendar events for courses"""
    events = []
    event_types = ["Lecture", "Tutorial", "Lab Session", "Exam", "Office Hours", "Review Session"]
    
    for course_id in course_ids:
        num_events = random.randint(*EVENTS_PER_COURSE)
        for _ in range(num_events):
            event_type = random.choice(event_types)
            title = f"{event_type}: {fake.word().capitalize()}"
            description = fake.sentence()
            event_date = fake.date_between(start_date='today', end_date='+4m')
            start_time = fake.time(pattern='%H:%M:00')
            duration = random.choice([1, 1.5, 2, 3])
            end_time = (datetime.strptime(start_time, '%H:%M:00') + 
                       timedelta(hours=duration)).strftime('%H:%M:00')
            created_by = random.choice(lecturer_user_ids)
            events.append((course_id, title, description, event_date, start_time, end_time, created_by))
    
    return events

def insert_events(events):
    """Insert calendar events into database"""
    sql = """INSERT INTO Calendar (crs_id, title, description, event_date, start_time, end_time, created_by, created_at) 
             VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())"""
    cursor.executemany(sql, events)
    db.commit()

def generate_course_content(course_ids, lecturer_user_ids):
    items = []
    for course_id in course_ids:
        num_sections = random.randint(*SECTIONS_PER_COURSE)
        for sec_num in range(1, num_sections + 1):
            title = f"Module {sec_num}: {fake.word().capitalize()}"
            created_by = random.choice(lecturer_user_ids)
            cursor.execute(
                "INSERT INTO Sections (crs_id, sec_num, title) VALUES (%s, %s, %s)",
                (course_id, sec_num, title)
            )
            section_id = cursor.lastrowid
            num_items = random.randint(*ITEMS_PER_SECTION)
            for item_num in range(1, num_items + 1):
                item_title = f"Content {item_num}: {fake.word().capitalize()}"
                item_type = random.choice(['slides', 'file', 'link'])
                if item_type == 'slides':
                    content_url = f"https://example.com/slides/{course_id}/{section_id}/{item_num}.pdf"
                    file_path = None
                elif item_type == 'file':
                    content_url = None
                    file_path = f"/uploads/course_{course_id}/section_{section_id}/item_{item_num}.pdf"
                else:
                    content_url = fake.uri()
                    file_path = None
                items.append((section_id, item_title, item_type, content_url, file_path, created_by))
    return items

def insert_content_items(items):
    """Insert content items into database"""
    sql = """INSERT INTO Section_Items (sec_id, title, item_type, content_url, file_path, created_by, created_at) 
             VALUES (%s, %s, %s, %s, %s, %s, NOW())"""
    cursor.executemany(sql, items)
    db.commit()

def ensure_default_admin():
    DEFAULT_ADMIN_ID = 1

    cursor.execute("SELECT 1 FROM Users WHERE acc_id=%s AND user_type='admin'", (DEFAULT_ADMIN_ID,))
    if cursor.fetchone() is None:
        pwd_hash = hash_password("ChangeMeNow!")
        cursor.execute("""
            INSERT INTO Users (acc_id, name, email, password, user_type)
            VALUES (%s, %s, %s, %s, %s)
        """, (DEFAULT_ADMIN_ID,
              "System Administrator",
              "admin@yourdomain.com",
              pwd_hash,
              "admin"))
        db.commit()
        print("  ↳ Inserted default admin (ID=1)")

def generate_sample_data():
    ensure_default_admin()

    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    tables = ["grades", "submissions", "assignments", "thread_Replies", "threads", "forums",
            "section_Items", "sections", "calendar", "student_Course", "courses", 
            "students", "lecturers", "admins", "users"]
    for table in tables:
        cursor.execute(f"TRUNCATE TABLE {table}")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    db.commit()

    print("Generating sample data...")

    # 1. Generate Admins (5)
    print("Creating admins...")
    admin_users = generate_users('admin', 5, start_index=0)
    fake.unique.clear()
    insert_users(admin_users)
    emails = [user[1] for user in admin_users]
    db.commit()

    # Fetch real acc_ids based on unique emails
    format_str = ','.join(['%s'] * len(emails))
    cursor.execute(f"SELECT acc_id FROM Users WHERE email IN ({format_str})", tuple(emails))
    admin_user_ids = [row[0] for row in cursor.fetchall()]

    # Now insert into Admins table safely
    admin_data = [(uid,) for uid in admin_user_ids]
    cursor.executemany("INSERT INTO Admins (acc_id) VALUES (%s)", admin_data)
    db.commit()

    # 2. Generate Lecturers (50)
    print(f"Creating {NUM_LECTURERS} lecturers...")
    lecturer_users = generate_users('lecturer', NUM_LECTURERS, start_index=100000)
    insert_users(lecturer_users)
    emails = [user[1] for user in lecturer_users]
    db.commit()

    # Fetch real acc_ids for these emails
    format_str = ','.join(['%s'] * len(emails))
    cursor.execute(f"SELECT acc_id FROM Users WHERE email IN ({format_str})", tuple(emails))
    lecturer_user_ids = [row[0] for row in cursor.fetchall()]

    # Now insert into Lecturers
    lecturer_data = [(uid,) for uid in lecturer_user_ids]
    cursor.executemany("INSERT INTO Lecturers (acc_id) VALUES (%s)", lecturer_data)
    db.commit()

    # 3. Generate Students (100,000 in optimized batches)
    print(f"Creating {NUM_STUDENTS} students in batches...")
    student_user_ids = []  # Track acc_id from Users
    student_st_ids = []    # Track st_id from Students
    batch_size = 5000

    fake.unique.clear()

    for batch_num in tqdm(range(0, NUM_STUDENTS, batch_size), desc="Generating students", unit="batch"):
        current_batch_size = min(batch_size, NUM_STUDENTS - batch_num)

        # 1. Generate students as Users
        student_users = generate_users('student', current_batch_size, start_index=batch_num)
        
        insert_users(student_users)
        emails = [user[1] for user in student_users]
        db.commit()

        # 2. Get acc_id values based on the unique emails
        format_str = ','.join(['%s'] * len(emails))
        cursor.execute(f"SELECT acc_id FROM Users WHERE email IN ({format_str})", tuple(emails))
        user_id_batch = [row[0] for row in cursor.fetchall()]
        student_user_ids.extend(user_id_batch)

        # 3. Insert into Students table
        student_data = [(acc_id,) for acc_id in user_id_batch]
        cursor.executemany("INSERT INTO Students (acc_id) VALUES (%s)", student_data)
        db.commit()

        # 4. Get st_id values from Students table
        format_str = ','.join(['%s'] * len(user_id_batch))
        cursor.execute(f"SELECT st_id FROM Students WHERE acc_id IN ({format_str})", tuple(user_id_batch))
        st_id_batch = [row[0] for row in cursor.fetchall()]
        student_st_ids.extend(st_id_batch)

    # 4. Create role records for lecturers
    print("Creating lecturer roles...")

    # Filter out any overlapping acc_ids
    lecturer_user_ids = [uid for uid in lecturer_user_ids if uid not in admin_user_ids]

    # Insert into Lecturers
    print("Fetching lecturer role IDs…")
    format_str = ','.join(['%s'] * len(lecturer_user_ids))
    cursor.execute(
        f"SELECT l_id FROM Lecturers WHERE acc_id IN ({format_str})",
        tuple(lecturer_user_ids)
    )
    lecturer_ids = [row[0] for row in cursor.fetchall()]

    # Fetch l_id values properly
    format_str = ','.join(['%s'] * len(lecturer_user_ids))
    cursor.execute(f"SELECT l_id FROM Lecturers WHERE acc_id IN ({format_str})", tuple(lecturer_user_ids))
    lecturer_ids = [row[0] for row in cursor.fetchall()]

    # 5. Generate Courses
    print(f"Creating {NUM_COURSES} courses...")
    courses = generate_courses(NUM_COURSES, lecturer_ids)
    fake.unique.clear()
    insert_courses(courses)

    cursor.execute("SELECT crs_id FROM Courses")
    course_ids = [row[0] for row in cursor.fetchall()]

    # # 6. Enroll students in courses
    print("Enrolling students in courses...")
    enrollments = enroll_students(course_ids, student_st_ids)
    insert_enrollments(enrollments)

    # 7. Generate Forums
    print("Creating forums...")
    forums = generate_forums(course_ids, lecturer_user_ids)
    insert_forums(forums)

    # 8. Generate Threads
    print("Creating discussion threads...")
    threads = generate_threads(forums, student_user_ids, lecturer_user_ids)
    insert_threads(threads)

    # 9. Generate Replies
    print("Creating thread replies...")
    replies = generate_replies(threads, student_user_ids, lecturer_user_ids)
    insert_replies(replies)

    # 10. Generate Assignments
    print("Creating assignments...")
    assignments = generate_assignments(course_ids, lecturer_user_ids)
    insert_assignments(assignments)

    # 11. Generate Submissions and Grades
    print("Creating submissions and grades...")
    submissions, grades = generate_submissions(assignments, student_st_ids)
    insert_submissions(submissions)
    insert_grades(grades)

    # 12. Generate Calendar Events
    print("Creating calendar events...")
    events = generate_events(course_ids, lecturer_user_ids)
    insert_events(events)

    # 13. Generate Course Content
    print("Creating course content...")
    content_items = generate_course_content(course_ids, lecturer_user_ids)
    insert_content_items(content_items)

    # Verification
    cursor.execute("SELECT COUNT(*) FROM Students")
    student_count = cursor.fetchone()[0]
    print(f"Verification: Created {student_count}/{NUM_STUDENTS} students")
    
    print("Data generation complete!")
    
if __name__ == "__main__":
    generate_sample_data()
    cursor.close()
    db.close()