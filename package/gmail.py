import os.path
import os
import json
import pytz
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from simplegmail import Gmail
from simplegmail.query import construct_query


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

    def __init__(self, client_secret_path="client_secret.json", credentials_path="credentials.json", force_renew=False) -> None:

        self.credentials_path = credentials_path
        self.client_secret_path = client_secret_path
        self._sheets_creds = None

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

        # spreadsheets setup
        self.__sheets_setup()

    def __generate_credentials(self):
        credentials = dict(json.load(open(self.client_secret_path)))
        # generate gmail_token.json
        self._gmail = Gmail(client_secret_file=self.client_secret_path)
        # merge gmail_token.json into the credentials dictionary then delete gmail_token.json
        credentials.update(json.load(open("gmail_token.json")))
        os.remove("gmail_token.json")
        # generate sheets credentials
        flow = InstalledAppFlow.from_client_secrets_file(
            self.client_secret_path, [
                "https://www.googleapis.com/auth/spreadsheets.readonly"]
        )
        self._sheets_creds = flow.run_local_server(port=0)
        # merge into credentials with a separted key i.e "sheets"
        credentials.update(
            {"sheets": json.loads(self._sheets_creds.to_json())})
        # save credentials to disk
        with open(self.credentials_path, "w") as file:
            file.write(json.dumps(credentials))
        return credentials

    def __get_credentials(self):
        with open(self.credentials_path) as file:
            return dict(json.load(file))

    def __check_is_expired(self):
        try:
            target_time_1 = datetime.fromisoformat(
                self.credentials["token_expiry"].replace('Z', '+00:00')).replace(tzinfo=pytz.UTC)
            target_time_2 = datetime.fromisoformat(
                self.credentials["sheets"]["expiry"].replace('Z', '+00:00')).replace(tzinfo=pytz.UTC)
        except KeyError:
            raise Exception(
                "Invalid credentials. Use GmailClient with force_renew=True")
        current_time = datetime.utcnow().replace(tzinfo=pytz.UTC)
        return current_time >= target_time_1 or current_time >= target_time_2

    def __gmail_setup(self):
        self._gmail = Gmail(
            client_secret_file=self.credentials_path, creds_file=self.credentials_path)
        self._query = construct_query(
            exact_phrase="meeting data from",
            sender="meetings-noreply@google.com",
            # TODO: Change this
            # unread=True,
            newer_than=(1, "Day"),
            # newer_than=(1, "Month"),
        )

    def __sheets_setup(self):
        self._sheets_creds = Credentials.from_authorized_user_info(
            self.credentials["sheets"], [
                "https://www.googleapis.com/auth/spreadsheets.readonly"])
        self._sheet = build(
            "sheets", "v4", credentials=self._sheets_creds).spreadsheets()

    def __format_date(self, date):
        date_obj = datetime.strptime(date, "%Y-%m-%d %H:%M:%S%z")
        return date_obj.strftime('%Y-%m-%d')

    def get_attendance(self):
        """every item will
        be a dictionary with key-value pairs (keys being the headers+Date+code)
        for every attendee there will be a different message appended"""

        messages = []
        for message in self._gmail.get_messages(query=self._query):

            link = message.html.split('href="')[1].split('"')[0]
            meeting_code = message.subject.split("'")[1]
            id = link.split("/")[5]

            data = list((
                self._sheet.values()
                .get(spreadsheetId=id, range="Attendees")
                .execute()
            ).get("values"))

            headers = data.pop(0)
            date = self.__format_date(message.date)

            for attendee in data:
                dict_ = {header: attendee[index]
                         for index, header in enumerate(headers)}
                dict_["Date"] = date
                dict_["Code"] = meeting_code
                messages.append(dict_)

        return messages


if __name__ == "__main__":
    gc = GmailClient(client_secret_path="secret.json", force_renew=False)
    # gc = GmailClient(client_secret_path="package/secret.json", credentials_path="credentials.json",
    #                  force_renew=True)
    for attendee in gc.get_attendance():
        print(attendee)