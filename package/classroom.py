import json
from datetime import datetime
from dateutil.relativedelta import relativedelta
from client import BaseClient


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


class Classroom(BaseClient):

    def __init__(
            self,
            client_secret_path="data/secret.json",
            credentials_path="data/credentials.json",
            courses_path="data/courses.json",
            force_renew=False
    ) -> None:
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

    @ staticmethod
    def is_older_than_one_month(datetime_str):
        input_datetime = datetime.fromisoformat(datetime_str[:-1])
        current_datetime = datetime.utcnow()
        one_month_ago = current_datetime - relativedelta(months=1)
        return input_datetime < one_month_ago

    def get_courses(self):
        courses: list[Course] = []
        results = self.service.courses().list(pageSize=10, pageToken=None).execute()
        next_token = results.get("nextPageToken")
        for course in results.get("courses", []):
            courses.append(Course(course))

        if courses:
            while next_token and not self.is_older_than_one_month(courses[-1].time_created):
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
