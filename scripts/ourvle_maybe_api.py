from flask import Flask, request, make_response
import mysql.connector

user = 'uwi_user'
password = 'uwi876'
host = '127.0.0.1'
database = 'course_management_system'

app = Flask(__name__)

@app.route('/reg_user', methods=['POST'])
def reg_user():
    try:
        cnx = mysql.connector.connect(user='uwi_user', password='uwi876',
                                    host='127.0.0.1',
                                    database='course_management_system')
        cursor = cnx.cursor()
        content = request.json
        acc_id = content['acc_id']
        name = content['name']
        email = content['email']
        password = content['password']
        user_type = content['user_type']

        cursor.execute(f"INSERT INTO users VALUES('{acc_id}', '{name}', '{email}', '{password}', '{user_type}')")

        if user_type == 'student':
            cursor.execute(f"INSERT INTO students VALUES('{acc_id}')")
        elif user_type == 'lecturer':
            cursor.execute(f"INSERT INTO lecturers VALUES('{acc_id}')")
        else:
            return make_response({'error': 'Invalid user type'}, 400)
        cnx.commit()
        cursor.close()
        cnx.close()
        return make_response({"success" : "user added"}, 201)
    except Exception as e:
        print(e)
        return make_response({'error': 'An error has occured'}, 400)

@app.route('/login', methods=['POST'])
def login():
    try:
        cnx = mysql.connector.connect(user='uwi_user', password='uwi876',
                                    host='127.0.0.1',
                                    database='course_management_system')
        cursor = cnx.cursor()
        content = request.json
        acc_id = content['acc_id']
        password = content['password']
        cursor.execute(f"SELECT * FROM users WHERE acc_id='{acc_id}' AND password='{password}'")
        row = cursor.fetchone()
        if row is not None:
            acc_id, name, email, password, user_type = row
            user = {}
            user['acc_id'] = acc_id
            user['name'] = name
            user['email'] = email
            user['password'] = password
            user['user_type'] = user_type
            cursor.close()
            cnx.close()
            return make_response(user, 200)
        else:
            return make_response({'error': 'Invalid credentials'}, 400)
        
    except Exception as e:
        return make_response({'error': str(e)}, 400)

@app.route('/create_course/<acc_id>', methods=['POST'])
def create_course(acc_id):
    try:
        cnx = mysql.connector.connect(user='uwi_user', password='uwi876',
                                host='127.0.0.1',
                                database='course_management_system')
        cursor = cnx.cursor()
        cursor.execute(f"SELECT * FROM admins WHERE acc_id='{acc_id}'")
        row = cursor.fetchone()
        if row is not None:
            content = request.json
            course_id = content['course_id']
            course_name = content['course_name']
            course_description = content['course_description']
            lecturer_id = content['lecturer_id']
            cursor.execute(f"INSERT INTO courses VALUES('{course_id}', '{course_name}', '{course_description}', '{lecturer_id}')")
            cnx.commit()
            cursor.close()
            cnx.close()
            return make_response({"success" : "Course created"}, 201)
        else:
            return make_response({'error': 'Invalid admin'}, 400)

    except Exception as e:
        return make_response({'error': str(e)}, 400)
    
@app.route('/courses', methods=['GET'])
def ret_course():
    try:
        cnx = mysql.connector.connect(user='uwi_user', password='uwi876',
                                host='127.0.0.1',
                                database='course_management_system')
        cursor = cnx.cursor()
        cursor.execute('SELECT * from courses')
        course_list = []
        rows = cursor.fetchall()
        for row in rows:
            course_id, course_name, course_description, lecturer_id = row
            course = {}
            course['CourseID'] = course_id
            course['CourseName'] = course_name
            course['CourseDescription'] = course_description
            course['LecturerID'] = lecturer_id
            course_list.append(course)
        cursor.close()
        cnx.close()
        return make_response(course_list, 200)

    except Exception as e:
        return make_response({'error': str(e)}, 400)
    
@app.route('/student/courses/<stu_id>', methods=['GET'])
def student_courses(stu_id):
    try:
        cnx = mysql.connector.connect(user='uwi_user', password='uwi876',
                                host='127.0.0.1',
                                database='course_management_system')
        cursor = cnx.cursor()
        cursor.execute(f"SELECT * FROM courses c JOIN register r ON c.crs_id = r.crs_id WHERE st_id = {stu_id}")
        course_list = []
        rows = cursor.fetchall()
        for row in rows:
            course_id, course_name, course_description, lecturer_id = row
            course = {}
            course['CourseID'] = course_id
            course['CourseName'] = course_name
            course['CourseDescription'] = course_description
            course['LecturerID'] = lecturer_id
            course_list.append(course)
    except Exception as e:
        return make_response({'error': str(e)}, 400)

@app.route('/lecturer/courses/<l_id>', methods=['GET'])
def lecturer_courses(l_id):
    try:
        cnx = mysql.connector.connect(user='uwi_user', password='uwi876',
                                host='127.0.0.1',
                                database='course_management_system')
        cursor = cnx.cursor()
        cursor.execute(f'SELECT * from courses WHERE lecturer_id = {l_id}')
        course_list = []
        rows = cursor.fetchall()
        for row in rows:
            course_id, course_name, course_description, lecturer_id = row
            course = {}
            course['CourseID'] = course_id
            course['CourseName'] = course_name
            course['CourseDescription'] = course_description
            course['LecturerID'] = lecturer_id
            course_list.append(course)
    except Exception as e:
        return make_response({'error': str(e)}, 400)

@app.route('/admin/assign_course', methods=['PUT'])
def assign_course():
    try:
        cnx = mysql.connector.connect(user='uwi_user', password='uwi876',
                                host='127.0.0.1',
                                database='course_management_system')
        cursor = cnx.cursor()
        content = request.json
        lec_id = content['lec_id']
        crs_id = content['crs_id']
        cursor.execute(f"SELECT COUNT(*) FROM courses WHERE lecturer_id ='{lec_id}'")
        row = cursor.fetchone()
        if row[0] < 5:
            cursor.execute(f"UPDATE courses SET lecturer_id = '{lec_id}' WHERE crs_id = '{crs_id}'")
            cnx.commit()
            cursor.close()
            cnx.close()
            return make_response({"success" : "Course assigned"}, 200)
        else:
            return make_response({'error': 'Lecturer has too many courses'}, 400)

    except Exception as e:
        return make_response({'error': str(e)}, 400)
    
@app.route('/student/register', methods=['POST'])
def register():
    try:
        cnx = mysql.connector.connect(user='uwi_user', password='uwi876',
                                host='127.0.0.1',
                                database='course_management_system')
        cursor = cnx.cursor()
        content = request.json
        stu_id = content['stu_id']
        crs_id = content['crs_id']
        cursor.execute(f"SELECT COUNT(*) FROM register WHERE st_id = '{stu_id}'")
        row = cursor.fetchone()
        if row[0] < 6:
            cursor.execute(f"INSERT INTO register (st_id, crs_id) VALUES ('{stu_id}', '{crs_id}')")
            cnx.commit()
            cursor.close()
            cnx.close()
            return make_response({"success" : "Course registered"}, 200)
        else:
            return make_response({'error': 'Student has too many courses'}, 400)

    except Exception as e:
        return make_response({'error': str(e)}, 400)
    
@app.route('/members/<course>', methods=['GET'])
def members(course):
    try:
        cnx = mysql.connector.connect(user='uwi_user', password='uwi876',
                                host='127.0.0.1',
                                database='course_management_system')
        cursor = cnx.cursor()
        cursor.execute(f"SELECT u.name  FROM register r JOIN students s ON r.st_id = s.st_id JOIN users u ON s.acc_id = u.acc_id WHERE r.crs_id = '{course}'")
        member_list = []
        rows = cursor.fetchall()
        for row in rows:
            name = row
            member = {}
            member['StudentName'] = name
            member_list.append(member)
        cursor.close()
        cnx.close()
        return make_response(member_list, 200)
    except Exception as e:
        return make_response({'error': str(e)}, 400)
    
@app.route('/ret_events/<course_id>', methods=['GET'])
def ret_events_course(course):
    try:
        cnx = mysql.connector.connect(user='uwi_user', password='uwi876',
                                host='127.0.0.1',
                                database='course_management_system')
        cursor = cnx.cursor()
        cursor.execute(f"SELECT * FROM calendar WHERE crs_id = '{course}'")
        calen_list = []
        rows = cursor.fetchall()
        for row in rows:
            cal_id, crs_id, title, description, event_date, start_time, end_time, created_by  = row
            calen = {}
            calen['CalendarId'] = cal_id
            calen['CourseId'] = crs_id
            calen['Title'] = title
            calen['Description'] = description
            calen['EventDate'] = event_date
            calen['StartTime'] = start_time
            calen['EndTime'] = end_time
            calen['CreatedBy'] = created_by
            calen_list.append(calen)
        cursor.close()
        cnx.close()
        return make_response(calen_list, 200)
    except Exception as e:
        return make_response({'error': str(e)}, 400)
    
@app.route('student/ret_events/<stu_id>', methods=['GET'])
def ret_events_date(stu_id):
    try:
        cnx = mysql.connector.connect(user='uwi_user', password='uwi876',
                                host='127.0.0.1',
                                database='course_management_system')
        cursor = cnx.cursor()
        content = request.json
        date = content['date']
        cursor.execute(f"SELECT * FROM calendar WHERE event_date = '{date}' AND crs_id IN (SELECT crs_id FROM register WHERE st_id = '{stu_id}')")
        calen_list = []
        rows = cursor.fetchall()
        for row in rows:
            cal_id, crs_id, title, description, event_date, start_time, end_time, created_by  = row
            calen = {}
            calen['CalendarId'] = cal_id
            calen['CourseId'] = crs_id
            calen['Title'] = title
            calen['Description'] = description
            calen['EventDate'] = event_date
            calen['StartTime'] = start_time
            calen['EndTime'] = end_time
            calen['CreatedBy'] = created_by
            calen_list.append(calen)
        cursor.close()
        cnx.close()
        return make_response(calen_list, 200)
    except Exception as e:
        return make_response({'error': str(e)}, 400)
    
@app.route('/create_event/<course>', methods=['POST'])
def create_event(course):
    try:
        cnx = mysql.connector.connect(user='uwi_user', password='uwi876',
                                host='127.0.0.1',
                                database='course_management_system')
        cursor = cnx.cursor()
        content = request.json
        title = content['title']
        description = content['description']
        event_date = content['event_date']
        start_time = content['start_time']
        end_time = content['end_time']
        created_by = content['created_by']
        cursor.execute(f"INSERT INTO calendar (crs_id, title, description, event_date, start_time, end_time, created_by) VALUES ('{course}', '{title}', '{description}', '{event_date}', '{start_time}', '{end_time}', '{created_by}')")
        cnx.commit()
        cursor.close()
        cnx.close()
        return make_response({"success" : "Calendar event created"}, 201)
        
    except Exception as e:
        return make_response({'error': str(e)}, 400)
    
@app.route('/ret_forums/<course>', methods=['GET'])
def ret_forums(course):
    try:
        cnx = mysql.connector.connect(user='uwi_user', password='uwi876',
                                host='127.0.0.1',
                                database='course_management_system')
        cursor = cnx.cursor()
        cursor.execute(f"SELECT * FROM forums WHERE crs_id = '{course}'")
        forum_list = []
        rows = cursor.fetchall()
        for row in rows:
            forum_id, crs_id, title, description, created_by  = row
            forum = {}
            forum['ForumId'] = forum_id
            forum['CourseId'] = crs_id
            forum['Title'] = title
            forum['Description'] = description
            forum['CreatedBy'] = created_by
            forum_list.append(forum)
    except Exception as e:
        return make_response({'error': str(e)}, 400)
    
@app.route('/create_forum/<course>', methods=['POST'])
def create_forum(course):
    try:
        cnx = mysql.connector.connect(user='uwi_user', password='uwi876',
                                host='127.0.0.1',
                                database='course_management_system')
        cursor = cnx.cursor()
        content = request.json
        title = content['title']
        description = content['description']
        created_by = content['created_by']
        cursor.execute(f"INSERT INTO forums (crs_id, title, description, created_by) VALUES ('{course}', '{title}', '{description}', '{created_by}')")
        cnx.commit()
        cursor.close()
        cnx.close()
        return make_response({"success" : "Forum created"}, 201)
    except Exception as e:
        return make_response({'error': str(e)}, 400)
    
@app.route('/threads/<forum>', methods=['GET'])
def ret_threads(forum):
    try:
        cnx = mysql.connector.connect(user='uwi_user', password='uwi876',
                                host='127.0.0.1',
                                database='course_management_system')
        cursor = cnx.cursor()
        cursor.execute(f"SELECT * FROM threads WHERE for_id = '{forum}'")
        thread_list = []
        rows = cursor.fetchall()
        for row in rows:
            t_id, for_id, title, content, created_by  = row
            thread = {}
            thread['ThreadId'] = t_id
            thread['ForumId'] = for_id
            thread['Title'] = title
            thread['Content'] = content
            thread['CreatedBy'] = created_by
            thread_list.append(thread)
    except Exception as e:
        return make_response({'error': str(e)}, 400)
    
@app.route('/create_thread/<forum>', methods=['POST'])
def create_thread(forum):
    try:
        cnx = mysql.connector.connect(user='uwi_user', password='uwi876',
                                host='127.0.0.1',
                                database='course_management_system')
        cursor = cnx.cursor()
        content = request.json
        title = content['title']
        content = content['content']
        created_by = content['created_by']
        cursor.execute(f"INSERT INTO threads (for_id, title, content, created_by) VALUES ('{forum}', '{title}', '{content}', '{created_by}')")
        cnx.commit()
        cursor.close()
        cnx.close()
        return make_response({"success" : "Thread created"}, 201)
        
    except Exception as e:
        return make_response({'error': str(e)}, 400)

@app.route('/reply/<thread>', methods=['POST'])
def reply(thread):
    try:
        cnx = mysql.connector.connect(user='uwi_user', password='uwi876',
                                host='127.0.0.1',
                                database='course_management_system')
        cursor = cnx.cursor()
        content = request.json
        parent_reply_id = content['parent_reply_id']
        user_id = content['user_id']
        content = content['content']
        cursor.execute(f"INSERT INTO replies (t_id, parent_reply_id, user_id, content) VALUES ('{thread}', '{parent_reply_id}', '{user_id}', '{content}')")
        cnx.commit()
        cursor.close()
        cnx.close()
        return make_response({"success" : "Reply created"}, 201)
    except Exception as e:
        return make_response({'error': str(e)}, 400)
    
@app.route('/section/<course>', methods=['POST'])
def create_section(course):
    try:
        cnx = mysql.connector.connect(user='uwi_user', password='uwi876',
                                host='127.0.0.1',
                                database='course_management_system')
        cursor = cnx.cursor()
        content = request.json
        section_number = content['section_number']
        title = content['title']
        cursor.execute(f"INSERT INTO sections (crs_id, sec_num, title) VALUES ('{course}', '{section_number}', '{title}')")
        cnx.commit()
        cursor.close()
        cnx.close()
        return make_response({"success" : "Section created"}, 201)
    except Exception as e:
        return make_response({'error': str(e)}, 400)
    
@app.route('/content/<section>', methods=['POST'])
def create_content(section):
    try:
        cnx = mysql.connector.connect(user='uwi_user', password='uwi876',
                                host='127.0.0.1',
                                database='course_management_system')
        cursor = cnx.cursor()
        content = request.json
        title = content['title']
        item_type = content['item_type']
        content_url = content['content_url']
        file_path = content['file_path']
        created_by = content['created_by']
        cursor.execute(f"INSERT INTO content (sec_id, title, item_type, content_url, file_path, created_by) VALUES ('{section}', '{title}', '{item_type}', '{content_url}', '{file_path}', '{created_by}')")
    except Exception as e:
        return make_response({'error': str(e)}, 400)
    
@app.route('/contents/<course>', methods=['GET'])
def ret_contents(course):
    try:
        cnx = mysql.connector.connect(user='uwi_user', password='uwi876',
                                host='127.0.0.1',
                                database='course_management_system')
        cursor = cnx.cursor()
        cursor.execute(f"SELECT s.sec_num, s.title, i.item_id, i.title, i.item_type, i.content_url, i.file_path, i.created_by FROM Sections s JOIN Section_Items i ON s.sec_id = i.sec_id WHERE s.crs_id = '{course}'")
        content_list = []
        rows = cursor.fetchall()
        for row in rows:
            sec_num, sTitle, item_id, iTitle, item_type, content_url, file_path, created_by  = row
            content = {}
            content['SectionNumber'] = sec_num
            content['SectionTitle'] = sTitle
            content['ItemId'] = item_id
            content['ItemTitle'] = iTitle
            content['ItemType'] = item_type
            content['ContentUrl'] = content_url
            content['FilePath'] = file_path
            content['CreatedBy'] = created_by
            content_list.append(content)
        cursor.close()
        cnx.close()
        return make_response(content_list, 200)
    except Exception as e:
        return make_response({'error': str(e)}, 400)
    
@app.route('/submit_assignment/<stu_id>', methods=['POST'])
def student_submit(stu_id):
    try:
        cnx = mysql.connector.connect(user='uwi_user', password='uwi876',
                                host='127.0.0.1',
                                database='course_management_system')
        data = request.json
        assign_id = data['assign_id']
        submission_text = data['submission_text']
        file_path = data['file_path']
        cursor = cnx.cursor()
        cursor.execute(f"INSERT INTO Submissions (assign_id, st_id, submission_text, file_path) VALUES ('{assign_id}','{stu_id}', '{submission_text}', '{file_path}')")
        cnx.commit()
        cursor.close()
        cnx.close()
        return make_response({"success": "Assignment submitted"}, 201)
    except Exception as e:
        return make_response({'error': str(e)}, 400)
    
@app.route('/grade_assignment/<sub_id>', methods=['POST'])
def grade_assignment(sub_id):
    try:
        cnx = mysql.connector.connect(user='uwi_user', password='uwi876',
                                      host='127.0.0.1',
                                      database='course_management_system')
        data = request.json
        score = data['score']
        feedback = data['feedback']
        graded_by = data['graded_by']
        cursor = cnx.cursor()
        cursor.execute(f"INSERT INTO Grades (submission_id, score, feedback, graded_by) VALUES ('{sub_id}', '{score}', '{feedback}', '{graded_by}')")
        cnx.commit()
        cursor.close()
        cnx.close() 
        return make_response({"success": "Assignment graded"}, 201)
    except Exception as e:
        return make_response({'error': str(e)}, 400)
    
@app.route('/average/st_id>', methods=['GET'])
def get_student_average(st_id):
    try:
        cnx = mysql.connector.connect(user='uwi_user', password='uwi876',
                                      host='127.0.0.1',
                                      database='course_management_system')
        cursor = cnx.cursor()
        cursor.execute(f"SELECT AVG(g.score) AS averageScore FROM Submissions s JOIN Grades g ON s.submission_id = g.submission_id WHERE s.st_id = {st_id}")
        result = cursor.fetchone()
        if result[0] is not None:
            average = result[0]  
        else:
            average = 0
        cursor.close()
        cnx.close()
        return make_response({"Student Id" : st_id, "average": average}, 200)
    except Exception as e:
        return make_response({'error': str(e)}, 400)
    
@app.route('/reports/courses_50', methods=['GET'])
def courses_with_50_or_more_students():
    try:
        cnx = mysql.connector.connect(user='uwi_user', password='uwi876',
                                      host='127.0.0.1',
                                      database='course_management_system')
        cursor = cnx.cursor()
        cursor.execute("SELECT * FROM courses_with_50_or_more_students")
        rows = cursor.fetchall()
        report = {}
        for row in rows:
            crs_id, name, student_count = row
            report.append({
                'CourseId': crs_id,
                'Name': name,
                'StudentCount': student_count
            })
        cursor.close()
        cnx.close()
        return make_response(report, 200)
    except Exception as e:
        return make_response({'error': str(e)}, 400)
    
@app.route('/reports/students_5_more', methods=['GET'])
def students_with_5_or_more_courses():
    try:
        cnx = mysql.connector.connect(user='uwi_user', password='uwi876',
                                      host='127.0.0.1',
                                      database='course_management_system')
        cursor = cnx.cursor()
        cursor.execute("SELECT * FROM students_with_5_or_more_courses")
        rows = cursor.fetchall()
        report = []
        for row in rows:
            acc_id, name, course_count = row
            report.append({
                'StudentId': acc_id,
                'Name': name,
                'CourseCount': course_count
            })
        cursor.close()
        cnx.close()
        return make_response(report, 200)
    except Exception as e:
        return make_response({'error': str(e)}, 400)

@app.route('/reports/lecturers_with_3', methods=['GET'])
def lecturers_with_3_or_more_courses():
    try:
        cnx = mysql.connector.connect(user='uwi_user', password='uwi876',
                                      host='127.0.0.1',
                                      database='course_management_system')
        cursor = cnx.cursor()
        cursor.execute("SELECT * FROM lecturers_with_3_or_more_courses")
        rows = cursor.fetchall()
        report = []
        for row in rows:
            acc_id, name, course_count = row
            report.append({
                'LecturerId': acc_id,
                'Name': name,
                'CourseCount': course_count
            })
        cursor.close()
        cnx.close()
        return make_response(report, 200)
    except Exception as e:
        return make_response({'error': str(e)}, 400)
    
@app.route('/reports/top_10_most_enrolled', methods=['GET'])
def top_10_most_enrolled_courses():
    try:
        cnx = mysql.connector.connect(user='uwi_user', password='uwi876',
                                      host='127.0.0.1',
                                      database='course_management_system')
        cursor = cnx.cursor()
        cursor.execute("SELECT * FROM top_10_most_enrolled_courses")
        rows = cursor.fetchall()
        report = []
        for row in rows:
            acc_id, name, enroll_count = row
            report.append({
                'StudentId': acc_id,
                'Name': name,
                'EnrollmentCount': enroll_count
            })
        cursor.close()
        cnx.close()
        return make_response(report, 200)
    except Exception as e:
        return make_response({'error': str(e)}, 400)
    
@app.route('/reports/top_10_students', methods=['GET'])
def top_10_students_by_average():
    try:
        cnx = mysql.connector.connect(user='uwi_user', password='uwi876',
                                      host='127.0.0.1',
                                      database='course_management_system')
        cursor = cnx.cursor()
        cursor.execute("SELECT * FROM top_10_students_by_average")
        rows = cursor.fetchall()
        report = []
        for row in rows:
            acc_id, name, average_score = row
            report.append({
                'StudentId': acc_id,
                'Name': name,
                'Average': average_score
            })
        cursor.close()
        cnx.close()
        return make_response(report, 200)
    except Exception as e:
        return make_response({'error': str(e)}, 400)