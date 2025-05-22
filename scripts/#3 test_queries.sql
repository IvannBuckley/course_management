USE `course_management_system`;

-- a) You must have at least 100,000 students.
SELECT COUNT(*) AS student_count
FROM Students;

-- b) You must have at least 200 courses.
SELECT COUNT(*) AS course_count
FROM Courses;

-- c) No student can do more than 6 courses.
SELECT st_id,
       COUNT(*) AS enrolled_courses
FROM Student_Course
GROUP BY st_id
HAVING enrolled_courses > 6;

-- d) A student must be enrolled in at least 3 courses.
SELECT st_id,
       COUNT(*) AS enrolled_courses
FROM Student_Course
GROUP BY st_id
HAVING enrolled_courses < 3;

-- e) Each course must have at least 10 members.
SELECT crs_id,
       COUNT(*) AS member_count
FROM Student_Course
GROUP BY crs_id
HAVING member_count < 10;

-- f) No lecturer can teach more than 5 courses.
SELECT lecturer_id,
       COUNT(*) AS courses_taught
FROM Courses
GROUP BY lecturer_id
HAVING courses_taught > 5;

-- g) A lecturer must teach at least 1 course.
-- This finds any lecturer with zero courses assigned
SELECT l.l_id,
       l.acc_id
FROM Lecturers AS l
LEFT JOIN Courses AS c
  ON c.lecturer_id = l.l_id
GROUP BY l.l_id
HAVING COUNT(c.crs_id) < 1;
