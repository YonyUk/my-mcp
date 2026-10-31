from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

from config import AppConfig

class GoogleDriveService:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(GoogleDriveService,cls).__new__(cls)
        return cls._instance

    @classmethod
    def get_service(cls):
        if not cls._instance:
            cls._instance = GoogleDriveService()
        return cls._instance

    def __init__(self):
        self._credentials = AppConfig.get_config().credentials
        self._service = build('drive','v3',credentials=self._credentials)

    async def upload_file(self,content:MediaIoBaseUpload,metadata:dict):
        file_link = self._service.files().create(
            body=metadata,
            media_body=content,
            fields="id,webViewLink"
        ).execute().get('webViewLink')
        return file_link