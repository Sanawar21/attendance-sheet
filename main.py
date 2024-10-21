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
        "Forcefully renew the API tokens? (y/n) "
    ).lower() == "y"

    env = get_env()

    username = env["SALESFORCE_USERNAME"]
    password = env["SALESFORCE_PASSWORD"]
    security_token = env["SALESFORCE_SECURITY_TOKEN"]

    gc = GmailClient(force_renew=force_renew)
    cc = ClassroomClient(force_renew=force_renew)
    ac = AttendanceClient(username, password, security_token)

    regen_db = input("Do you wish to regenerate the students and courses database? (Not recommended; takes a lot of time; irreversible; cannot stop before completion) (y/n) ").lower() == "y"

    if regen_db:

        if input("Do you wish to continue? (y/n)").lower() == "y":
            print("Generating the database...")
            cc.generate_database()
            print("Database regenerated successfully.")
            quit()

    print("Getting attendees...")
    attendees = gc.get_attendees()
    print("Getting absentees...")
    absentees = cc.get_absentees(attendees)

    missing_courses = []

    for attendee in attendees:
        if attendee["Course"] == None:
            course_code = ""
            try:
                name_code = "-".join([x for x in attendee["Last name"][::-1].split("-")
                                      if x[0] not in "abcdefghijklmnopqrstuvwxyz "])[::-1].strip()
                attrs = name_code.split("-")
                attrs.pop(3)
                course_code = "-".join(attrs)
            except IndexError:
                pass
            if not course_code:
                course_code = None
            missing_courses.append(course_code)
            attendee["Course"] = course_code

    print(f"Missing courses: {list(set(missing_courses))}")
    print("This may be due to these courses being older than or newer than the database\ngeneration period. ")
    print("Auto setting them to course code extracted from attendee names.")

    print()

    print("Uploading to salesforce...")

    for attendee in attendees:
        ac.upload(attendee)
        print(
            f'Uploaded attendance for {attendee["Last name"]} (Course: {attendee["Course"]})'
        )

    # Create a set of unique keys for attendees using Course ID, Last name, and Date
    attendees_set = {
        (attendee["Course ID"], attendee["Last name"].strip(), attendee["Date"])
        for attendee in attendees
    }

    for absentee in absentees:
        # Create a key for each absentee
        absentee_key = (absentee["Course ID"],
                        absentee["Last name"].strip(), absentee["Date"])

        # Check if this absentee is not in the attendees set
        if absentee_key not in attendees_set:
            ac.upload(absentee)
            print(
                f'Uploaded absence for {absentee["Last name"]} (Course: {absentee["Course"]})')
