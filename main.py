# create a python env with python 3.10 called attendance: 'python -m venv attendance'
# activate python env: 'attendance\Scripts\activate'
# install requirements: 'pip install -r requirements.txt'
# run program: 'python main.py'

# After creating and running for the first time, activate the env again and run the program.

from package.gmail import GmailClient
from package.salesforce import AttendanceClient


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
    env = get_env()

    username = env["SALESFORCE_USERNAME"]
    password = env["SALESFORCE_PASSWORD"]
    security_token = env["SALESFORCE_SECURITY_TOKEN"]

    gc = GmailClient()
    ac = AttendanceClient(username, password, security_token)

    for attendee in gc.get_attendance():
        ac.upload(attendee)
        print(
            f"Uploaded attendance for {attendee['Code']} (Course: {attendee['Course']})")
