import random
from faker import Faker
import hashlib
import string
from datetime import datetime, timedelta
from tqdm import tqdm

fake = Faker()

# Constants
NUM_STUDENTS = 100000
NUM_COURSES = 200
NUM_LECTURERS = 50
MIN_COURSES_PER_STUDENT = 3
MAX_COURSES_PER_STUDENT = 6
MIN_STUDENTS_PER_COURSE = 10
MAX_LECTURER_COURSES = 5

# Where we’ll collect our SQL
sql_statements = []

def escape(s: str) -> str:
    """Simple single-quote escaper for SQL literals."""
    return "'" + s.replace("'", "''") + "'"

def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def generate_random_password(length=12):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(chars) for _ in range(length))

def sql_insert(table: str, columns: list[str], values: tuple):
    cols = ", ".join(columns)
    vals = ", ".join(escape(v) if isinstance(v, str) else str(v) for v in values)
    sql_statements.append(f"INSERT INTO {table} ({cols}) VALUES ({vals});")

def generate_users(user_type: str, count: int, start_id: int) -> list[int]:
    """Return the list of assigned acc_ids for this batch."""
    acc_ids = []
    for i in range(count):
        acc_id = start_id + i
        name   = fake.name()
        email  = f"{user_type}{acc_id}@example.com"
        pwd    = hash_password(generate_random_password())
        sql_insert(
            "Users",
            ["acc_id","name","email","password","user_type"],
            (acc_id, name, email, pwd, user_type)
        )
        acc_ids.append(acc_id)
    return acc_ids

def generate_lecturers(lecturer_ids: list[int]):
    for l_id in lecturer_ids:
        sql_insert("Lecturers", ["acc_id"], (l_id,))

def generate_students(student_ids: list[int]):
    for acc_id in student_ids:
        sql_insert("Students", ["acc_id"], (acc_id,))

def generate_courses(course_ids: list[int], lecturer_ids: list[int]):
    lec_counts = {lid:0 for lid in lecturer_ids}
    courses = []
    # first ensure each lecturer has 1
    for idx, lid in enumerate(lecturer_ids):
        cid = course_ids[idx]
        name = fake.sentence(nb_words=3).replace("'", "")
        desc = fake.text(max_nb_chars=100).replace("'", "")
        courses.append((cid,name,desc,lid))
        lec_counts[lid]+=1
    # rest
    for cid in course_ids[len(lecturer_ids):]:
        avail = [l for l,c in lec_counts.items() if c<MAX_LECTURER_COURSES]
        lid   = random.choice(avail)
        name = fake.sentence(nb_words=3).replace("'", "")
        desc = fake.text(max_nb_chars=100).replace("'", "")
        courses.append((cid,name,desc,lid))
        lec_counts[lid]+=1

    for cid,name,desc,lid in courses:
        sql_insert("Courses", ["crs_id","name","crs_des","lecturer_id"], (cid,name,desc,lid))

def generate_enrollments(course_ids: list[int], student_ids: list[int]):
    scount = {sid:0 for sid in student_ids}
    ccount = {cid:0 for cid in course_ids}
    enrolls = []

    # each student in 3–6 random
    for sid in student_ids:
        n = random.randint(MIN_COURSES_PER_STUDENT, MAX_COURSES_PER_STUDENT)
        picks = random.sample(course_ids, n)
        for cid in picks:
            enrolls.append((sid,cid))
            scount[sid]+=1
            ccount[cid]+=1

    # top up any course <10
    for cid in course_ids:
        if ccount[cid] < MIN_STUDENTS_PER_COURSE:
            needed = MIN_STUDENTS_PER_COURSE - ccount[cid]
            cands = [s for s in student_ids if scount[s]<MAX_COURSES_PER_STUDENT]
            for sid in random.sample(cands, needed):
                enrolls.append((sid,cid))
                scount[sid]+=1
                ccount[cid]+=1

    for sid,cid in enrolls:
        sql_insert("Student_Course", ["st_id","crs_id"], (sid,cid))

# … similarly, you can write small generators for Forums, Threads, etc. …

if __name__ == "__main__":
    # 1) default admin
    sql_insert("Users", ["acc_id","name","email","password","user_type"],
               (1, "Sys Admin", "admin@school.com",
                hash_password("ChangeMe"), "admin"))
    # 2) lecturers
    lec_ids = generate_users("lecturer", NUM_LECTURERS, start_id=1000)
    generate_lecturers(lec_ids)

    # 3) students
    stud_ids = generate_users("student", NUM_STUDENTS, start_id=100000)
    generate_students(stud_ids)

    # 4) courses
    course_ids = list(range(1, NUM_COURSES+1))
    generate_courses(course_ids, lec_ids)

    # 5) enrollments
    generate_enrollments(course_ids, stud_ids)

    # … other tables …

    # finally, write them out
    with open("seed_data.sql", "w", encoding="utf8") as f:
        f.write("USE course_management_system;\n")
        f.write("SET FOREIGN_KEY_CHECKS = 0;\n")
        f.write("TRUNCATE TABLE Users;\nTRUNCATE TABLE Lecturers;\nTRUNCATE TABLE Students;\nTRUNCATE TABLE Courses;\nTRUNCATE TABLE Student_Course;\n")
        f.write("SET FOREIGN_KEY_CHECKS = 1;\n\n")
        f.write("\n".join(sql_statements))

    print("Wrote seed_data.sql with", len(sql_statements), "statements.")
