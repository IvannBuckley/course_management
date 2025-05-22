import random
from faker import Faker
import hashlib
import string
from datetime import datetime, timedelta
from tqdm import tqdm

# Initialize Faker
dummy = Faker()

# Constants based on requirements
NUM_STUDENTS = 1000 #set to 1000 for space purposes, 1000,000 students resulted in a 24gb file which could not be uploaded
NUM_COURSES = 200
NUM_LECTURERS = 50
MIN_COURSES_PER_STUDENT = 3
MAX_COURSES_PER_STUDENT = 6
MIN_STUDENTS_PER_COURSE = 10
MAX_LECTURER_COURSES = 5

# Feature constants
FORUMS_PER_COURSE = (1, 3)
THREADS_PER_FORUM = (5, 15)
REPLIES_PER_THREAD = (0, 10)
ASSIGNMENTS_PER_COURSE = (3, 8)
EVENTS_PER_COURSE = (5, 12)
SECTIONS_PER_COURSE = (4, 8)
ITEMS_PER_SECTION = (3, 7)

# Collector for SQL statements
sql_statements = []

# Helpers
def escape(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"

def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def gen_insert(table: str, cols: list, vals: tuple):
    col_list = ",".join(cols)
    val_list = ",".join(
        escape(v) if isinstance(v, str)
        else f"'{v.isoformat(sep=' ')}'" if isinstance(v, datetime)
        else str(v)
        for v in vals
    )
    sql_statements.append(f"INSERT INTO {table}({col_list}) VALUES({val_list});")

def flush_sql(filename='seed_data.sql'):
    """
    Append current sql_statements to file and clear buffer
    """
    with open(filename, 'a', encoding='utf8') as f:
        for stmt in sql_statements:
            f.write(stmt + '\n')
    sql_statements.clear()

# 1) Users, Admin, Lecturer, Student
def gen_users(user_type, count, start_id):
    ids = []
    for i in tqdm(range(count), desc=f"Generating {user_type}s", unit="user"):
        acc = start_id + i
        name = dummy.name().replace("'", "")
        email = f"{user_type}{acc}@example.com"
        pwd = hash_password(dummy.password(length=12, special_chars=True))
        gen_insert("Users", ["acc_id","name","email","password","user_type"],
                   (acc, name, email, pwd, user_type))
        ids.append(acc)
    flush_sql()
    return ids

# 2) Lecturers & Students tables reference acc_id
def gen_lecturers(acc_ids):
    for acc in tqdm(acc_ids, desc="Inserting Lecturers", unit="lecturer"):
        gen_insert("Lecturers", ["acc_id"], (acc,))
    flush_sql()

def gen_students(acc_ids):
    for acc in tqdm(acc_ids, desc="Inserting Students", unit="student"):
        gen_insert("Students", ["acc_id"], (acc,))
    flush_sql()

# 3) Courses with explicit crs_id
def gen_courses(course_ids, lecturer_ids):
    lec_count = {l:0 for l in lecturer_ids}
    assignments = []
    for idx, lid in enumerate(tqdm(lecturer_ids, desc="Assigning initial Courses", unit="lecturer")):
        cid = course_ids[idx]
        name = dummy.word().capitalize() + " " + dummy.word().capitalize()
        desc = dummy.text(max_nb_chars=100).replace("'", "")
        assignments.append((cid, name, desc, lid))
        lec_count[lid] += 1
    for cid in tqdm(course_ids[len(lecturer_ids):], desc="Distributing Courses", unit="course"):
        avail = [l for l,c in lec_count.items() if c < MAX_LECTURER_COURSES]
        lid = random.choice(avail)
        name = dummy.word().capitalize() + " " + dummy.word().capitalize()
        desc = dummy.text(max_nb_chars=100).replace("'", "")
        assignments.append((cid, name, desc, lid))
        lec_count[lid] += 1
    for cid, nm, ds, lid in tqdm(assignments, desc="Generating Course INSERTs", unit="course"):
        gen_insert("Courses", ["crs_id","name","crs_des","lecturer_id"], (cid, nm, ds, lid))
    flush_sql()

# 4) Student_Course enrollments
def gen_enrollments(course_ids, student_ids):
    stu_c = {s:0 for s in student_ids}
    crs_c = {c:0 for c in course_ids}
    recs = []
    for s in tqdm(student_ids, desc="Assigning initial Enrollments", unit="student"):
        n = random.randint(MIN_COURSES_PER_STUDENT, MAX_COURSES_PER_STUDENT)
        picks = random.sample(course_ids, n)
        for c in picks:
            recs.append((s,c)); stu_c[s]+=1; crs_c[c]+=1
    for c in tqdm(course_ids, desc="Top-up Enrollments", unit="course"):
        need = max(0, MIN_STUDENTS_PER_COURSE - crs_c[c])
        if need:
            cands = [s for s in student_ids if stu_c[s] < MAX_COURSES_PER_STUDENT]
            for s in random.sample(cands, need):
                recs.append((s,c)); stu_c[s]+=1; crs_c[c]+=1
    for s,c in tqdm(recs, desc="Generating Enrollment INSERTs", unit="enrollment"):
        gen_insert("Student_Course", ["st_id","crs_id"], (s,c))
    flush_sql()

# 5) Forums, Threads, Replies
def gen_forums(course_ids, lecturer_ids, start_id=1):
    fid = start_id
    fids = []
    for c in tqdm(course_ids, desc="Generating Forums", unit="course"):
        for _ in range(random.randint(*FORUMS_PER_COURSE)):
            title = dummy.sentence(nb_words=3).replace("'","")
            desc = dummy.sentence().replace("'","")
            by = random.choice(lecturer_ids)
            gen_insert("Forums", ["forum_id","crs_id","title","description","created_by","date_created"],
                       (fid, c, title, desc, by, datetime.now()))
            fids.append(fid); fid+=1
    flush_sql()
    return fids

def gen_threads(forum_ids, user_ids, start_id=1):
    tid = start_id
    tids = []
    for f in tqdm(forum_ids, desc="Generating Threads", unit="forum"):
        for _ in range(random.randint(*THREADS_PER_FORUM)):
            title = dummy.sentence(nb_words=5).replace("'","")
            content = dummy.paragraph(nb_sentences=2).replace("'","")
            by = random.choice(user_ids)
            gen_insert("Threads", ["thread_id","forum_id","title","content","created_by","created_at"],
                       (tid, f, title, content, by, datetime.now()))
            tids.append(tid); tid+=1
    flush_sql()
    return tids

def gen_replies(thread_ids, user_ids, start_id=1):
    rid = start_id
    for t in tqdm(thread_ids, desc="Generating Replies", unit="thread"):
        for _ in range(random.randint(*REPLIES_PER_THREAD)):
            parent = None
            if random.random() < 0.3 and rid>start_id:
                parent = random.randint(start_id, rid-1)
            txt = dummy.paragraph(nb_sentences=1).replace("'","")
            by = random.choice(user_ids)
            gen_insert("Thread_Replies", ["t_id","parent_reply_id","user_id","content","created_at"],
                       (t, parent, by, txt, datetime.now()))
            rid+=1
    flush_sql()

# 6) Assignments & Submissions/Grades
def gen_assignments(course_ids, lecturer_ids, start_id=1):
    aid = start_id; aids = []
    for c in tqdm(course_ids, desc="Generating Assignments", unit="course"):
        for _ in range(random.randint(*ASSIGNMENTS_PER_COURSE)):
            title = f"Assignment: {dummy.word().capitalize()}"
            desc = dummy.text(max_nb_chars=80).replace("'","")
            due = datetime.now() + timedelta(days=random.randint(1,90))
            ms = random.choice([10,20,30,50,100])
            by = random.choice(lecturer_ids)
            gen_insert("Assignments", ["assign_id","crs_id","title","description","due_date","max_score","created_by","created_at"],
                       (aid, c, title, desc, due, ms, by, datetime.now()))
            aids.append(aid); aid+=1
    flush_sql()
    return aids

def gen_submissions_grades(assign_ids, student_ids, lecturer_ids, sub_start=1, grade_start=1):
    sid = sub_start; gid = grade_start
    for a in tqdm(assign_ids, desc="Generating Submissions & Grades", unit="assignment"):
        studs = random.sample(student_ids, int(len(student_ids)*0.7))
        for s in studs:
            txt = dummy.text(max_nb_chars=100).replace("'","")
            fp = f"/uploads/{a}_{s}.pdf"
            gen_insert("Submissions", ["submission_id","assign_id","st_id","submission_text","file_path","submitted_at"],
                       (sid, a, s, txt, fp, datetime.now()))
            if random.random() < 0.8:
                sc = round(random.uniform(50,100),2)
                fb = dummy.sentence(nb_words=4).replace("'","")
                by = random.choice(lecturer_ids)
                gen_insert("Grades", ["grade_id","submission_id","score","feedback","graded_by","graded_at"],
                           (gid, sid, sc, fb, by, datetime.now()))
                gid+=1
            sid+=1
    flush_sql()

# 7) Calendar events
def gen_events(course_ids, lecturer_ids, start_id=1):
    eid = start_id
    for c in tqdm(course_ids, desc="Generating Events", unit="course"):
        for _ in range(random.randint(*EVENTS_PER_COURSE)):
            typ = random.choice(["Lecture","Tutorial","Lab","Exam","Office","Review"])
            title = f"{typ} {dummy.word().capitalize()}"
            desc = dummy.sentence().replace("'","")
            dt = datetime.now() + timedelta(days=random.randint(1,120))
            start = dt.time().strftime("%H:%M:%S")
            end = (dt + timedelta(hours=random.choice([1,2,3]))).time().strftime("%H:%M:%S")
            by = random.choice(lecturer_ids)
            gen_insert("Calendar", ["event_id","crs_id","title","description","event_date","start_time","end_time","created_by","created_at"],
                       (eid, c, title, desc, dt.date(), start, end, by, datetime.now()))
            eid+=1
    flush_sql()

# 8) Sections & Items
def gen_sections_items(course_ids, lecturer_ids, sec_start=1, item_start=1):
    sid = sec_start; iid = item_start
    for c in tqdm(course_ids, desc="Generating Sections & Items", unit="course"):
        for num in range(1, random.randint(*SECTIONS_PER_COURSE)+1):
            title = f"Module {num} {dummy.word().capitalize()}"
            gen_insert("Sections", ["sec_id","crs_id","sec_num","title"], (sid, c, num, title))
            for it in range(1, random.randint(*ITEMS_PER_SECTION)+1):
                kind = random.choice(['slides','file','link'])
                url = f"https://slides/{c}/{sid}/{it}.pdf" if kind=='slides' else None
                fp  = f"/uploads/{c}_{sid}_{it}.pdf" if kind=='file' else None
                by = random.choice(lecturer_ids)
                gen_insert("Section_Items", ["item_id","sec_id","title","item_type","content_url","file_path","created_by","created_at"],
                           (iid, sid, f"Content {it}", kind, url, fp, by, datetime.now()))
                iid+=1
            sid+=1
    flush_sql()

# Main
def main():
    # Setup file
    open('seed_data.sql', 'w').close()

    sql_statements.append("USE course_management_system;")
    sql_statements.append("SET FOREIGN_KEY_CHECKS = 0;")
    for t in ["Grades","Thread_Replies","Threads","Forums","Calendar","Section_Items","Sections","Assignments","Submissions","Student_Course","Courses","Students","Lecturers","Users"]:
        sql_statements.append(f"TRUNCATE TABLE {t};")
    sql_statements.append("SET FOREIGN_KEY_CHECKS = 1;")
    flush_sql()

    admin = gen_users('admin', 1, 1)
    lecs  = gen_users('lecturer', NUM_LECTURERS, 1000)
    gen_lecturers(lecs)
    studs = gen_users('student', NUM_STUDENTS, 100000)
    gen_students(studs)

    crs = list(range(1, NUM_COURSES+1))
    gen_courses(crs, lecs)
    gen_enrollments(crs, studs)

    fids = gen_forums(crs, lecs)
    tids = gen_threads(fids, studs+lecs)
    gen_replies(tids, studs+lecs)

    aids = gen_assignments(crs, lecs)
    gen_submissions_grades(aids, studs, lecs)

    gen_events(crs, lecs)
    gen_sections_items(crs, lecs)

if __name__=='__main__':
    main()
