import os
import json
import pytz
from datetime import datetime
from simplegmail import Gmail
from simplegmail.query import construct_query
from .sheets import SheetsClient


class GmailClient:
    """
    Initializes the gmail API for getting the
    attendence sheets as soon as they are created. 

    This client is meant to be run a few times a day so new credentials are
    generated each time it is run. So I have added an optional parameter to 
    force the renewal of credentials.

    When the GmailCLient object is created, user will pass the client_secret
    that can be downloaded from the workspace OAuth.
    After that, the program will check for a credentials.json file.
    If it is not found, the program will generate it using the client_secret.json
    and if it is found, the program will run.

    """

    def __init__(self, client_secret_path="data/secret.json", credentials_path="data/credentials.json", courses_path="data/courses.json", force_renew=False) -> None:

        self.credentials_path = credentials_path
        self.client_secret_path = client_secret_path
        self.courses_path = courses_path

        # check if credentials.json is available
        try:
            with open(self.credentials_path):
                credentials_available = True
        except FileNotFoundError:
            credentials_available = False

        if not credentials_available or force_renew:
            self.credentials = self.__generate_credentials()
        else:
            self.credentials = self.__get_credentials()
            if self.__check_is_expired():
                self.credentials = self.__generate_credentials()

        # gmail setup
        self.__gmail_setup()

        self.sheets = SheetsClient(force_renew=force_renew)

    def __generate_credentials(self):
        credentials = dict(json.load(open(self.client_secret_path)))
        # generate gmail_token.json
        self._gmail = Gmail(client_secret_file=self.client_secret_path)
        # merge gmail_token.json into the credentials dictionary then delete gmail_token.json
        credentials.update(json.load(open("gmail_token.json")))
        os.remove("gmail_token.json")
        # save credentials to disk
        with open(self.credentials_path, "w") as file:
            file.write(json.dumps(credentials))
        return credentials

    def __get_credentials(self):
        with open(self.credentials_path) as file:
            return dict(json.load(file))

    def __check_is_expired(self):
        try:
            target = datetime.fromisoformat(
                self.credentials["token_expiry"].replace('Z', '+00:00')).replace(tzinfo=pytz.UTC)
        except KeyError:
            raise Exception(
                "Invalid credentials. Use GmailClient with force_renew=True")
        current_time = datetime.utcnow().replace(tzinfo=pytz.UTC)
        return current_time >= target

    def __gmail_setup(self):
        self._gmail = Gmail(
            client_secret_file=self.credentials_path, creds_file=self.credentials_path)
        self._query = construct_query(
            exact_phrase="Meeting records from",
            sender="meetings-noreply@google.com",
            # TODO: Change this
            # after="2024/06/06",
            # before="2024/06/14"
            # unread=False,
            # read=True,
            newer_than=(1, "Day"),
            # newer_than=(1, "Month"),
        )

    @staticmethod
    def format_date(date):
        date_obj = datetime.strptime(date, "%Y-%m-%d %H:%M:%S%z")
        return date_obj.strftime('%Y-%m-%d')

    def get_attendees(self):
        """every item will
        be a dictionary with key-value pairs (keys being the headers+Date+code)
        for every attendee there will be a different message appended"""

        messages = []
        courses = [value for value in list(json.load(
            open(self.courses_path)).values())]

        gmail_messages = self._gmail.get_messages(query=self._query)

        for message in gmail_messages:
            try:
                half_link = "https://docs.google.com/spreadsheets/d"
                link = half_link + \
                    message.html.split(half_link)[1].split("\"")[0]
            except IndexError:
                print(f"No attendance sheet found. Skipping message.")
                continue
            spreadsheetId = link.split("/")[5]
            data = self.sheets.get_spreadsheet(spreadsheetId)
            if not data:
                print(
                    f"Failed to get data from {spreadsheetId}. Skipping message.")
                continue
            meeting_code = data["title"].split(" ")[2]
            data = data["data"]
            headers = data.pop(0)
            date = self.format_date(message.date)

            for attendee in data:
                if len(attendee) == 6:
                    dict_ = {header: attendee[index]
                             for index, header in enumerate(headers)}
                    dict_["Date"] = date
                    dict_["Code"] = meeting_code

                    for course in courses:
                        if course["meet_link"]:
                            if meeting_code in course["meet_link"]:
                                dict_["Course"] = course["description"]
                                dict_["Course ID"] = course["id"]
                                break
                    else:
                        dict_["Course"] = None
                        dict_["Course ID"] = None

                    messages.append(dict_)
                else:
                    print("Invalid attendee attributes.")

            print(f"Collected attendees for {meeting_code}")
            message.mark_as_read()

        return messages
