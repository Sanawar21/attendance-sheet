import json
from datetime import datetime, timezone
from .client import BaseClient


class Student:

    def __init__(self, student) -> None:
        try:
            self.course_id = student["courseId"]
        except KeyError:
            self.course_id = None
        try:
            self.full_name = student["profile"]["name"]["fullName"]
        except KeyError:
            self.full_name = None

    def as_dict(self):
        return {
            "course_id": self.course_id,
            "full_name": self.full_name
        }


class Course:
    def __init__(self, course) -> None:
        self.name = course["name"]
        self.id = course["id"]
        self.link = course["alternateLink"]
        try:
            self.description = course["description"]
        except KeyError:
            self.description = None
        try:
            self.room = course["room"]
        except KeyError:
            self.room = None
        self.meet_link = self.room
        self.time_created = course["creationTime"]

    def as_dict(self):
        course_dict = {
            "id": self.id,
            "name": self.name,
            "link": self.link,
            "description": self.description,
            "meet_link": self.meet_link,
            "time_created": self.time_created,
        }
        return course_dict


class ClassroomClient(BaseClient):
    def __init__(
            self,
            classes_start_date="01/04/2024",
            client_secret_path="data/secret.json",
            credentials_path="data/credentials.json",
            courses_path="data/courses.json",
            students_path="data/students.json",
            force_renew=False
    ) -> None:
        """
        classes_start_date format: dd/mm/yyyy e.g "01/04/2024"
        """
        super().__init__(
            "classroom",
            "v1",
            client_secret_path,
            credentials_path,
            courses_path,
            [
                "https://www.googleapis.com/auth/classroom.courses.readonly",
                "https://www.googleapis.com/auth/classroom.rosters.readonly",
            ],
            force_renew
        )
        self.classes_start_date = classes_start_date
        self.students_path = students_path

    def is_since_start_date(self, date: str) -> bool:
        from_date = datetime.strptime(
            self.classes_start_date, "%d/%m/%Y").replace(tzinfo=timezone.utc)
        iso_date = datetime.fromisoformat(date.replace(
            'Z', '+00:00')).replace(tzinfo=timezone.utc)

        return iso_date > from_date

    def get_courses(self):
        courses: list[Course] = []
        results = self.service.courses().list(pageSize=10, pageToken=None).execute()
        next_token = results.get("nextPageToken")
        for course in results.get("courses", []):
            courses.append(Course(course))

        if courses:
            while next_token and self.is_since_start_date(courses[-1].time_created):
                results = self.service.courses().list(
                    pageSize=10, pageToken=next_token).execute()
                next_token = results.get("nextPageToken")
                for course in results.get("courses", []):
                    courses.append(Course(course))

        return courses

    def get_students(self, courseId):
        # implement and save in new data.json and ask in init whether or reload the db or not
        students: list[Student] = []
        results = self.service.courses().students().list(
            courseId=courseId, pageSize=10, pageToken=None).execute()
        next_token = results.get("nextPageToken")
        for student in results.get("students", []):
            students.append(Student(student))

        if students:
            while next_token:
                results = self.service.courses().students().list(
                    courseId=courseId, pageSize=10, pageToken=next_token).execute()
                next_token = results.get("nextPageToken")
                for student in results.get("students", []):
                    students.append(Student(student))

        return students

    def save(self, iterable: list[Student | Course]):
        if iterable:
            if type(iterable[0]) == Student:
                data = {iterable[0].course_id: [
                    student.full_name for student in iterable]}
                path = "data/students.json"
            elif type(iterable[0]) == Course:
                data = {course.id: course.as_dict() for course in iterable}
                path = "data/courses.json"

            try:
                with open(path) as file:
                    old_data = json.loads(file.read())
            except (FileNotFoundError, json.decoder.JSONDecodeError):
                old_data = {}

            with open(path, "w") as file:
                old_data.update(data)
                file.write(json.dumps(old_data))

    def generate_database(self):
        courses = self.get_courses()
        self.save(courses)
        for course in courses:
            students = self.get_students(course.id)
            self.save(students)

    def get_absentees(self, attendees):
        # attendee {
        #     'Course ID': 'adsfadfadsf',
        #     'First name': 'Sanawar',
        #     'Last name': 'Saeed',
        #     'Email': 'test@g.com',
        #     'Duration': '56 min',
        #     'Time joined': '10:30\u202fPM',
        #     'Time exited': '11:25\u202fPM',
        #     'Date': '2024-05-4T23:26:18+05:00Z',
        #     'Code': 'dnf-fkqv-twc',
        #     'Course': 'Course 1'
        # }

        # absentee {
        #     'Course ID': 'adsfadfadsf',
        #     'First name': 'Sanawar',
        #     'Last name': 'Saeed',
        #     'Course': 'Course 1',
        #     'Date': '2024-05-4T23:26:18+05:00Z'
        # }

        absentees = []
        course_attendees = {}
        for attendee in attendees:
            course_id = attendee["Course ID"]

            try:
                course_attendees[course_id].append(attendee)
            except KeyError:
                course_attendees[course_id] = [attendee]

        students = json.load(open(self.students_path))
        courses = json.load(open(self.courses_path))

        for course_id, attendees_info in course_attendees.items():
            if not course_id:
                continue

            try:
                course_students = students[course_id]
            except KeyError:
                print(
                    f"No students list found in database linked with {course_id}")
                print(f"Cannot fetch absentees for {course_id}")
                print(f"Recommended to regenerate the database.")
                continue

            course_attendee_students = [student for student in course_students if any(
                [attendee_info["Last name"] in student for attendee_info in attendees_info])]
            course_absentee_students = list(
                set(course_students) - set(course_attendee_students))

            for absentee_name in course_absentee_students:
                reversed_name = absentee_name[::-1]
                flag = False
                last_name = ""

                for chr in reversed_name:
                    if flag and chr == " ":
                        last_name = last_name[::-1]
                        break
                    if chr in "abcdefghijklmnopqrstuvwxyz":
                        flag = True
                    last_name += chr
                else:
                    last_name = absentee_name.split(" ")[-1]

                first_name = absentee_name[:absentee_name.index(
                    last_name)].strip()

                absentees.append({
                    "First name": first_name,
                    "Last name": last_name,
                    "Course ID": course_id,
                    "Course": courses[course_id]["description"],
                    "Date": attendees_info[0]["Date"],
                })

            print(
                f'Collected absentees for {courses[course_id]["meet_link"].split("/")[-1]}')

        return absentees
