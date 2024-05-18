# create a python env with python 3.10 called attendance: 'python -m venv attendance'
# activate python env: 'attendance\Scripts\activate'
# install requirements: 'pip install -r requirements.txt'
# run program: 'python main.py'

# After creating and running for the first time, activate the env again and run the program.

from package.gmail import GmailClient
from package.salesforce import AttendanceClient
from package.classroom import ClassroomClient


def get_env():
    env_dict = {}
    with open(".env", "r") as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env_dict[key.strip()] = value.strip()
    return env_dict


if __name__ == "__main__":
    print("Welcome To Attendence Sheet Bot")
    force_renew = input(
        "Forcefully renew the API tokens? (y/n) ").lower() == "y"
    env = get_env()

    username = env["SALESFORCE_USERNAME"]
    password = env["SALESFORCE_PASSWORD"]
    security_token = env["SALESFORCE_SECURITY_TOKEN"]

    gc = GmailClient(force_renew=force_renew)
    cc = ClassroomClient(force_renew=force_renew)
    ac = AttendanceClient(username, password, security_token)
    attendees = gc.get_attendees()
    absentees = cc.get_absentees(attendees)

    for attendee in attendees:
        ac.upload(attendee)
        print(
            f"Uploaded attendance for {attendee["Last name"]} (Course: {attendee['Course']})"
        )

    for absentee in absentees:
        ac.upload(absentee)
        print(
            f"Uploaded absence for {absentee["Last name"]} (Course: {absentee['Course']})"
        )
