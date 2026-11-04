from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import threading

from config import AppConfig

class GoogleDriveService:
    _instance = None
    _lock = threading.Lock()
    _local = threading.local()

    def __new__(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(GoogleDriveService,cls).__new__(cls)
        return cls._instance

    @classmethod
    def get_service(cls):
        if not cls._instance:
            cls._instance = GoogleDriveService()
        return cls._instance

    def __init__(self):
        if not getattr(self,'_service') is None:
            return

    @property
    def _service(self):
        if not hasattr(self._local,'service'):
            self._credentials = AppConfig.get_config().credentials
            self._local.service = build('drive','v3',credentials=self._credentials)
        return self._local.service
    
    def upload_file(self,content:MediaIoBaseUpload,metadata:dict):
        file_link = self._service.files().create(
            body=metadata,
            media_body=content,
            fields="id,webViewLink"
        ).execute().get('webViewLink')
        return file_link