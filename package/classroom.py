import os.path
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
SCOPES = ["https://www.googleapis.com/auth/classroom.courses.readonly"]


class Classroom:
    # TODO: separate class for gmail, classroom and sheets
    pass


class Course:
    def __init__(self, course, meet_link=None) -> None:
        self.name = course["name"]
        self.link = course["alternateLink"]
        try:
            self.description = course["description"]
        except KeyError:
            print(course)
            self.description = None
        try:
            self.room = course["room"]
        except KeyError:
            self.room = None
        self.meet_link = meet_link

    def as_dict(self):
        course_dict = {
            "name": self.name,
            "link": self.link,
            "description": self.description,
            "meet_link": self.meet_link,
            "room": self.room,
        }
        return course_dict


creds = None
if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            "data/secret.json", SCOPES
        )
        creds = flow.run_local_server(port=0)

    with open("token.json", "w") as token:
        token.write(creds.to_json())

service = build("classroom", "v1", credentials=creds)
results = service.courses().list(pageSize=10, pageToken=None).execute()
next_token = results.get("nextPageToken")
courses = results.get("courses", [])
if not courses:
    print("No courses found.")
print("Courses:")
for course in courses:
    print(course["name"])

course_dicts = []
results = service.courses().list(pageSize=10).execute()
pageToken = results.get("nextPageToken")
courses = results.get("courses", [])
while pageToken:
    results = service.courses().list(pageSize=10, pageToken=pageToken).execute()
    courses = results.get("courses", [])
    for course in courses:
        course_dicts.append(Course(course).as_dict())
    pageToken = results.get("nextPageToken")
