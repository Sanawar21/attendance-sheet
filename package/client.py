import json
import pytz
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime


class BaseClient:
    def __init__(
            self,
            service_name,
            build_version,
            client_secret_path,
            credentials_path,
            courses_path,
            scopes,
            force_renew
    ) -> None:
        self.credentials_path = credentials_path
        self.client_secret_path = client_secret_path
        self.courses_path = courses_path
        self._creds = None
        self.scopes = scopes
        self.service_name = service_name
        self.build_version = build_version

        os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

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

        # run setup
        self.__setup()

    def __get_credentials(self):
        with open(self.credentials_path) as file:
            return dict(json.load(file))

    def __generate_credentials(self):
        credentials = dict(json.load(open(self.credentials_path)))
        flow = InstalledAppFlow.from_client_secrets_file(
            self.client_secret_path, self.scopes
        )
        self._creds = flow.run_local_server(port=0)

        credentials.update(
            {self.service_name: json.loads(self._creds.to_json())}
        )
        with open(self.credentials_path, "w") as file:
            file.write(json.dumps(credentials))
        return credentials

    def __setup(self):
        self._creds = Credentials.from_authorized_user_info(
            self.credentials[self.service_name], self.scopes)
        self.service = build(
            self.service_name, self.build_version, credentials=self._creds)

    def __check_is_expired(self):
        try:
            target = datetime.fromisoformat(
                self.credentials[self.service_name]["expiry"].replace('Z', '+00:00')).replace(tzinfo=pytz.UTC)
        except KeyError:
            raise Exception(
                f"Invalid credentials. Use {self.service_name} client with force_renew=True")
        current_time = datetime.utcnow().replace(tzinfo=pytz.UTC)
        return current_time >= target
