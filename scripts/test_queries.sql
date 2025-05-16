USE `course_management_system`;

-- a) You must have at least 100,000 students.
SELECT COUNT(*) AS student_count
FROM Students;
-- Ensure student_count >= 100000


-- b) You must have at least 200 courses.
SELECT COUNT(*) AS course_count
FROM Courses;
-- Ensure course_count >= 200


-- c) No student can do more than 6 courses.
SELECT st_id,
       COUNT(*) AS enrolled_courses
FROM Student_Course
GROUP BY st_id
HAVING enrolled_courses > 6;
-- Any rows returned here are students in >6 courses


-- d) A student must be enrolled in at least 3 courses.
SELECT st_id,
       COUNT(*) AS enrolled_courses
FROM Student_Course
GROUP BY st_id
HAVING enrolled_courses < 3;
-- Any rows returned here are students in <3 courses


-- e) Each course must have at least 10 members.
SELECT crs_id,
       COUNT(*) AS member_count
FROM Student_Course
GROUP BY crs_id
HAVING member_count < 10;
-- Any rows returned here are courses with <10 students


-- f) No lecturer can teach more than 5 courses.
SELECT lecturer_id,
       COUNT(*) AS courses_taught
FROM Courses
GROUP BY lecturer_id
HAVING courses_taught > 5;
-- Any rows returned here are lecturers teaching >5 courses


-- g) A lecturer must teach at least 1 course.
-- This finds any lecturer with zero courses assigned
SELECT l.l_id,
       l.acc_id
FROM Lecturers AS l
LEFT JOIN Courses AS c
  ON c.lecturer_id = l.l_id
GROUP BY l.l_id
HAVING COUNT(c.crs_id) < 1;
-- Any rows returned here are lecturers teaching 0 courses
