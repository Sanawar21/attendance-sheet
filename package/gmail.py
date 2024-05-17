import os
import json
import pytz
from datetime import datetime
from simplegmail import Gmail
from simplegmail.query import construct_query
from sheets import SheetsClient


class GmailClient:
    """
    Initializes the gmail and spreadsheets API for getting the
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

    def __init__(self, sheets: SheetsClient, client_secret_path="data/secret.json", credentials_path="data/credentials.json", courses_path="data/courses.json", force_renew=False) -> None:

        self.credentials_path = credentials_path
        self.client_secret_path = client_secret_path
        self.courses_path = courses_path
        self.sheets = sheets

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
            exact_phrase="meeting data from",
            sender="meetings-noreply@google.com",
            # TODO: Change this
            unread=True,
            newer_than=(1, "Day"),
            # newer_than=(1, "Month"),
        )

    @staticmethod
    def __format_date(date):
        date_obj = datetime.strptime(date, "%Y-%m-%d %H:%M:%S%z")
        return date_obj.strftime('%Y-%m-%d')

    def get_attendance(self):
        """every item will
        be a dictionary with key-value pairs (keys being the headers+Date+code)
        for every attendee there will be a different message appended"""

        messages = []
        courses = json.load(open(self.courses_path))
        for message in self._gmail.get_messages(query=self._query):

            link = message.html.split('href="')[1].split('"')[0]
            meeting_code = message.subject.split("'")[1]
            spreadsheetId = link.split("/")[5]
            data = self.sheets.get_spreadsheet(spreadsheetId)

            headers = data.pop(0)
            date = self.__format_date(message.date)

            for attendee in data:
                dict_ = {header: attendee[index]
                         for index, header in enumerate(headers)}
                dict_["Date"] = date
                dict_["Code"] = meeting_code

                for course in courses:
                    if meeting_code in course["meet_link"]:
                        dict_["Course"] = course["description"]
                        break
                else:
                    dict_["Course"] = None

                messages.append(dict_)

            message.mark_as_read()

        return messages
