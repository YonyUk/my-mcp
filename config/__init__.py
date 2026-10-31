import os
import json
from typing import List
from dotenv import load_dotenv

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

load_dotenv()

class NoGmailScopesProvidedException(Exception):
    pass

class NoGmailCredentialsProvidedException(Exception):
    pass

class NoGmailTokenFilePathProvided(Exception):
    pass

class NoGmailApiCredentialsFlowPortProvided(Exception):
    pass

class CredentialsRefreshingException(Exception):
    pass

class NoApifyApiTokenProvided(Exception):
    pass

class NoApifyUserIdProvided(Exception):
    pass

class NoApifyActorIdProvided(Exception):
    pass

class NoGoogleDriveOutputFolderIdProvided(Exception):
    pass

class AppConfig:

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(AppConfig, cls).__new__(cls)
        return cls._instance

    @classmethod
    def get_config(cls):
        if cls._instance is None:
            cls._instance = AppConfig()
        return cls._instance

    def __init__(self) -> None:
        
        self._gmail_api_scopes:List[str] = json.loads(os.getenv('GMAIL_API_SCOPES','[]'))
        if not self._gmail_api_scopes:
            raise NoGmailScopesProvidedException()
        gmail_api_credentials_path:List[str] = json.loads(os.getenv('GMAIL_API_CREDENTIALS_PATH','[]'))
        if not gmail_api_credentials_path:
            raise NoGmailCredentialsProvidedException()
        gmail_api_token_file_path:List[str] = json.loads(os.getenv('GMAIL_API_TOKEN_FILE_PATH','[]'))
        if not gmail_api_token_file_path:
            raise NoGmailTokenFilePathProvided()
        gmail_api_credentials_flow_port:int = None # type: ignore
        try:
            gmail_api_credentials_flow_port:int = int(os.getenv('GMAIL_API_FLOW_PORT',''))
        except ValueError:
            raise NoGmailApiCredentialsFlowPortProvided()
        if gmail_api_credentials_flow_port < 0:
            raise ValueError('gmail_api_credentials_flow_port can\'t be less than 0')
        self._apify_api_token:str = os.getenv('REDDIT_APIFY_API_TOKEN','')
        if not self._apify_api_token:
            raise NoApifyApiTokenProvided()
        self._apify_user_id:str = os.getenv('REDDIT_APIFY_USER_ID','')
        if not self._apify_user_id:
            raise NoApifyUserIdProvided()
        self._apify_actor_id:str = os.getenv('REDDIT_APIFY_ACTOR_ID','')
        if not self._apify_actor_id:
            raise NoApifyActorIdProvided()
        self._output_folder_id:str = os.getenv('GOOGLE_DRIVE_OUTPUT_FOLDER_ID','')
        if not self._output_folder_id:
            raise NoGoogleDriveOutputFolderIdProvided()
        self._credentials:Credentials = None # type: ignore
        credentials_path = os.path.join(*gmail_api_credentials_path)
        token_file_path = os.path.join(*gmail_api_token_file_path)

        if os.path.exists(token_file_path):
            self._credentials = Credentials.from_authorized_user_file(token_file_path,self._gmail_api_scopes)

        if not self._credentials or not self._credentials.valid:
            if self._credentials and self._credentials.expired and self._credentials.refresh_token:
                try:
                    self._credentials.refresh(Request())
                except Exception as ex:
                    raise CredentialsRefreshingException()
            else:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path,self._gmail_api_scopes)
                self._credentials = flow.run_local_server(port=gmail_api_credentials_flow_port) # type: ignore

            with open(token_file_path,'w') as f:
                f.write(self._credentials.to_json())

    @property
    def credentials(self) -> Credentials:
        return self._credentials

    @property
    def apify_api_token(self) -> str:
        return self._apify_api_token

    @property
    def apify_user_id(self) -> str:
        return self._apify_user_id

    @property
    def apify_actor_id(self) -> str:
        return self._apify_actor_id

    @property
    def output_folder_id(self) -> str:
        return self._output_folder_id