# create a python env with python 3.10 called attendance: 'python -m venv attendance'
# activate python env: 'attendance/Scripts/activate.bat'
# install requirements: 'pip install -r requirements.txt'
# run program: 'python main.py'

# After creating and running for the first time, activate the env again and run the program.

import os
from package.gmail import GmailClient
from package.salesforce import AttendanceClient
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    username = os.getenv("SALESFORCE_USERNAME").strip(
        "'").rstrip(",").rstrip("'")
    password = os.getenv("SALESFORCE_PASSWORD").strip(
        "'").rstrip(",").rstrip("'")
    security_token = os.getenv(
        "SALESFORCE_SECURITY_TOKEN").strip("'").rstrip(",").rstrip("'")

    gc = GmailClient("secret.json")
    ac = AttendanceClient(username, password, security_token)

    for attendee in gc.get_attendance():
        ac.upload(attendee)
        print(f"Uploaded attendance for {attendee['Code']}")
