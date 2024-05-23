from .client import BaseClient


class SheetsClient(BaseClient):

    def __init__(
            self,
            client_secret_path="data/secret.json",
            credentials_path="data/credentials.json",
            courses_path="data/courses.json",
            force_renew=False
    ) -> None:
        super().__init__(
            "sheets",
            "v4",
            client_secret_path,
            credentials_path,
            courses_path,
            [
                "https://www.googleapis.com/auth/spreadsheets.readonly"
            ],
            force_renew
        )

    def get_spreadsheet(self, spreadsheetId, range_="Attendees"):
        while True:
            try:
                return list(
                    (self
                     .service
                     .spreadsheets()
                     .values()
                     .get(spreadsheetId=spreadsheetId, range=range_)
                     .execute()
                     )
                    .get("values"))

            except TimeoutError:
                print("Google spreadsheets' read operation timed out, trying again.")
