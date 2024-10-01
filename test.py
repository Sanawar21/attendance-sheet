from package.classroom import ClassroomClient
from package.gmail import GmailClient
from package.salesforce import AttendanceClient
from package.sheets import SheetsClient

from main import get_env

username = get_env()["SALESFORCE_USERNAME"]
password = get_env()["SALESFORCE_PASSWORD"]
security_token = get_env()["SALESFORCE_SECURITY_TOKEN"]

force_renew = True

gc = GmailClient(force_renew=force_renew)
cc = ClassroomClient(force_renew=force_renew)
ac = AttendanceClient(username, password, security_token)


submissions = []
coursework = cc.service.courses().courseWork()
response = coursework.studentSubmissions().list(
    courseId="695918984719",
    courseWorkId="-",
    pageSize=10).execute()
submissions.extend(response.get('studentSubmissions', []))

if not submissions:
    print('No student submissions found.')

print('Student Submissions:')
for submission in submissions:
    print(f"Submitted at:"
          f"{(submission.get('userId'), submission.get('assignedGrade'))}")
