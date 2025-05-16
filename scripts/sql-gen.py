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

# Collector for SQL statements
sql_statements = []

def escape(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"

def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def sql_insert(table: str, cols: list[str], vals: tuple):
    col_list = ", ".join(cols)
    val_list = ", ".join(
        escape(v) if isinstance(v, str) else
        (v.isoformat(sep=' ') if isinstance(v, datetime) else str(v))
        for v in vals
    )
    sql_statements.append(f"INSERT INTO {table} ({col_list}) VALUES ({val_list});")

# --- User, Lecturer, Student Generators ---
def gen_users(user_type: str, count: int, start_id: int) -> list[int]:
    ids = []
    for i in range(count):
        uid = start_id + i
        name = fake.name()
        email = f"{user_type}{uid}@example.com"
        pwd = hash_password(fake.password(length=12, special_chars=True))
        sql_insert("Users", ["acc_id","name","email","password","user_type"],
                   (uid, name, email, pwd, user_type))
        ids.append(uid)
    return ids

def gen_lecturers(ids: list[int]):
    for uid in ids:
        sql_insert("Lecturers", ["acc_id"], (uid,))

def gen_students(ids: list[int]):
    for uid in ids:
        sql_insert("Students", ["acc_id"], (uid,))

# --- Course Generator ---
def gen_courses(course_ids: list[int], lecturer_ids: list[int]):
    lec_count = {l:0 for l in lecturer_ids}
    courses = []
   
    for idx, lid in enumerate(lecturer_ids):
        cid = course_ids[idx]
        name = fake.sentence(nb_words=3).replace("'", "")
        desc = fake.text(max_nb_chars=100).replace("'", "")
        courses.append((cid,name,desc,lid))
        lec_count[lid] += 1
   
    for cid in course_ids[len(lecturer_ids):]:
        avail = [l for l,c in lec_count.items() if c < MAX_LECTURER_COURSES]
        lid = random.choice(avail)
        name = fake.sentence(nb_words=3).replace("'", "")
        desc = fake.text(max_nb_chars=100).replace("'", "")
        courses.append((cid,name,desc,lid))
        lec_count[lid] += 1
    for cid,name,desc,lid in courses:
        sql_insert("Courses", ["crs_id","name","crs_des","lecturer_id"],
                   (cid,name,desc,lid))
    return course_ids

# --- Enrollment Generator ---
def gen_enrollments(course_ids: list[int], student_ids: list[int]):
    stu_count = {s:0 for s in student_ids}
    crs_count = {c:0 for c in course_ids}
    records = []
   
    for sid in student_ids:
        n = random.randint(MIN_COURSES_PER_STUDENT, MAX_COURSES_PER_STUDENT)
        picks = random.sample(course_ids, n)
        for cid in picks:
            records.append((sid,cid))
            stu_count[sid]+=1; crs_count[cid]+=1
  
    for cid in course_ids:
        need = max(0, MIN_STUDENTS_PER_COURSE - crs_count[cid])
        if need>0:
            cands = [s for s in student_ids if stu_count[s] < MAX_COURSES_PER_STUDENT]
            for sid in random.sample(cands, need):
                records.append((sid,cid))
                stu_count[sid]+=1; crs_count[cid]+=1
    for sid,cid in records:
        sql_insert("Student_Course", ["st_id","crs_id"], (sid,cid))
    return records

# --- Forum, Thread, Reply Generators ---
def gen_forums(course_ids: list[int], lecturer_ids: list[int]) -> list[int]:
    forum_ids = []
    fid = 1
    for cid in course_ids:
        for _ in range(random.randint(1,3)):
            title = fake.sentence(nb_words=4).replace("'","")
            desc = fake.text(max_nb_chars=80).replace("'","")
            by = random.choice(lecturer_ids)
            created = fake.date_time_between(start_date='-1y', end_date='now')
            sql_insert("Forums", ["forum_id","crs_id","title","description","created_by","date_created"],
                       (fid, cid, title, desc, by, created))
            forum_ids.append(fid)
            fid+=1
    return forum_ids

def gen_threads(forum_ids: list[int], student_ids: list[int], lecturer_ids: list[int]) -> list[int]:
    thread_ids=[]; tid=1
    for fid in forum_ids:
        for _ in range(random.randint(5,15)):
            title = fake.sentence(nb_words=6).replace("'","")
            content = fake.paragraph(nb_sentences=3).replace("'","")
            by = random.choice(student_ids+lecturer_ids)
            at = fake.date_time_between(start_date='-6m', end_date='now')
            sql_insert("Threads", ["thread_id","forum_id","title","content","created_by","created_at"],
                       (tid, fid, title, content, by, at))
            thread_ids.append(tid)
            tid+=1
    return thread_ids

def gen_replies(thread_ids: list[int], user_ids: list[int]) -> None:
    rid=1
    for tid in thread_ids:
        for _ in range(random.randint(0,10)):
            parent=None
            if random.random()<0.3:
                parent = random.choice([r for r in range(1,rid)])
            content = fake.paragraph(nb_sentences=2).replace("'","")
            by = random.choice(user_ids)
            at = fake.date_time_between(start_date='-3m', end_date='now')
            sql_insert("Thread_Replies", ["reply_id","thread_id","parent_reply_id","user_id","content","created_at"],
                       (rid, tid, parent, by, content, at))
            rid+=1

# --- Assignment & Submission Generators ---
def gen_assignments(course_ids: list[int], lecturer_ids: list[int]) -> list[int]:
    assign_ids=[]; aid=1
    for cid in course_ids:
        for i in range(random.randint(3,8)):
            title = f"Assignment {i+1}: {fake.word().capitalize()}"
            desc = fake.text(max_nb_chars=80).replace("'","")
            due = fake.date_time_between(start_date='now', end_date='+3M')
            score = random.choice([10,20,30,50,100])
            by = random.choice(lecturer_ids)
            sql_insert("Assignments", ["assign_id","crs_id","title","description","due_date","max_score","created_by","created_at"],
                       (aid, cid, title, desc, due, score, by, datetime.now()))
            assign_ids.append(aid)
            aid+=1
    return assign_ids

def gen_submissions_grades(assign_ids: list[int], student_ids: list[int], lecturer_ids: list[int]) -> None:
    sub_id=1; grade_id=1
    for aid in assign_ids:
        enrolled = random.sample(student_ids, k=int(len(student_ids)*0.7))
        for sid in enrolled:
            text = fake.paragraph(nb_sentences=3).replace("'","")
            path = f"/uploads/assignment_{aid}_student_{sid}.pdf"
            at = datetime.now()
            sql_insert("Submissions", ["submission_id","assign_id","st_id","submission_text","file_path","submitted_at"],
                       (sub_id, aid, sid, text, path, at))
           
            if random.random()<0.8:
                score = round(random.uniform(50,100),2)
                fb = fake.sentence(nb_words=4).replace("'","")
                by = random.choice(lecturer_ids)
                at2 = datetime.now()
                sql_insert("Grades", ["grade_id","submission_id","score","feedback","graded_by","graded_at"],
                           (grade_id, sub_id, score, fb, by, at2))
                grade_id+=1
            sub_id+=1

# --- Events & Content Generators ---
def gen_events(course_ids: list[int], lecturer_ids: list[int]) -> None:
    eid=1
    types = ["Lecture","Tutorial","Lab","Exam","Office","Review"]
    for cid in course_ids:
        for _ in range(random.randint(5,12)):
            typ = random.choice(types)
            title = f"{typ}: {fake.word().capitalize()}"
            desc = fake.sentence().replace("'","")
            date = fake.date_time_between(start_date='now', end_date='+4M')
            start = date.strftime("%H:%M:%S")
            end   = (date + timedelta(hours=random.choice([1,1.5,2,3]))).strftime("%H:%M:%S")
            by = random.choice(lecturer_ids)
            sql_insert("Calendar", ["event_id","crs_id","title","description","event_date","start_time","end_time","created_by","created_at"],
                       (eid, cid, title, desc, date.date(), start, end, by, datetime.now()))
            eid+=1

def gen_sections_items(course_ids: list[int], lecturer_ids: list[int]) -> None:
    sec_id=1; item_id=1
    for cid in course_ids:
        for s in range(1, random.randint(4,8)+1):
            title = f"Module {s}: {fake.word().capitalize()}"
            by = random.choice(lecturer_ids)
            sql_insert("Sections", ["sec_id","crs_id","sec_num","title","created_at"],
                       (sec_id, cid, s, title, datetime.now()))
            for it in range(1, random.randint(3,7)+1):
                kind = random.choice(['slides','file','link'])
                url = (f"https://example.com/slides/{cid}/{sec_id}/{it}.pdf" if kind=='slides' else None)
                fp  = (None if kind=='slides' else f"/uploads/course_{cid}/s_{sec_id}/item_{it}.pdf")
                sql_insert("Section_Items", ["item_id","sec_id","title","item_type","content_url","file_path","created_by","created_at"],
                           (item_id, sec_id, f"Content {it}", kind, url, fp, by, datetime.now()))
                item_id+=1
            sec_id+=1

# --- Main ---
if __name__ == '__main__':

    sql_statements.append("USE course_management_system;")
    sql_statements.append("SET FOREIGN_KEY_CHECKS = 0;")
    for t in ["Grades","Thread_Replies","Threads","Forums","Calendar","Section_Items","Sections","Assignments","Submissions","Student_Course","Courses","Students","Lecturers","Users"]:
        sql_statements.append(f"TRUNCATE TABLE {t};")
    sql_statements.append("SET FOREIGN_KEY_CHECKS = 1;")
  
    admin_ids = gen_users('admin', 1, 1)
    lec_ids   = gen_users('lecturer', NUM_LECTURERS, 1000)
    gen_lecturers(lec_ids)
    stu_ids   = gen_users('student', NUM_STUDENTS, 100000)
    gen_students(stu_ids)

    crs_ids = list(range(1, NUM_COURSES+1))
    gen_courses(crs_ids, lec_ids)

    gen_enrollments(crs_ids, stu_ids)
    forum_ids = gen_forums(crs_ids, lec_ids)
    thread_ids = gen_threads(forum_ids, stu_ids, lec_ids)
    gen_replies(thread_ids, stu_ids + lec_ids)

    assign_ids = gen_assignments(crs_ids, lec_ids)
    gen_submissions_grades(assign_ids, stu_ids, lec_ids)
    gen_events(crs_ids, lec_ids)
    gen_sections_items(crs_ids, lec_ids)

    # Write SQL file
    with open('seed_data.sql','w',encoding='utf8') as f:
        f.write('\n'.join(sql_statements))
    print(f"Wrote seed_data.sql with {len(sql_statements)} statements.")
