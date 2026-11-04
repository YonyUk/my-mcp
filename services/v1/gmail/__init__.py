import base64
import re
import threading
from typing import Any, Dict, Iterable, List, Tuple
from googleapiclient.discovery import build

from config import AppConfig

class Header:

    def __init__(self,name:str,value:str) -> None:
        self._name = name
        self._value = value

    @property
    def name(self) -> str:
        return self._name

    @property
    def value(self) -> str:
        return self._value

class Payload:

    def __init__(self,partId:str,mime_type:str,filename:str,headers:Dict[str,str],body:Dict[str,str]):
        self._partId = partId
        self._mime_type = mime_type
        self._filename = filename
        self._headers = [Header(h['name'],h['value']) for h in headers] # type: ignore
        self._body = body
        self._text_body_mime_type_re = 'text/(plain|html)'

    @property
    def partId(self) -> str:
        return self._partId

    @property
    def mime_type(self) -> str:
        return self._mime_type

    @property
    def filename(self) -> str:
        return self._filename

    @property
    def headers(self) -> List[Header]:
        return self._headers

    @property
    def body(self) -> Any:
        if re.fullmatch(self._text_body_mime_type_re,self._mime_type) and 'data' in self._body:
            data = self._body['data']
            body = base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
            return body.strip()
        raise NotImplementedError()

class Mail:

    def __init__(
        self,
        mail_id:str,
        threadId:str,
        labelIds:List[str],
        snippet:str,
        sizeEstimate:int,
        historyId:str,
        internalDate:str,
        headers:Dict[str,str],
        content:List[Payload]
    ):
        self._id = mail_id
        self._threadId = threadId
        self._snippet = snippet
        self._labelIds = labelIds
        self._sizeEstimate = sizeEstimate
        self._historyId = historyId
        self._internalDate = internalDate
        self._content = content
        self._headers = [Header(h['name'],h['value']) for h in headers] # type: ignore

    @property
    def id(self) -> str:
        return self._id

    @property
    def threadId(self) -> str:
        return self._threadId

    @property
    def snippet(self) -> str:
        return self._snippet

    @property
    def labelIds(self) -> List[str]:
        return self._labelIds

    @property
    def sizeEstimate(self) -> int:
        return self._sizeEstimate

    @property
    def historyId(self) -> str:
        return self._historyId

    @property
    def internalDate(self) -> str:
        return self._internalDate

    @property
    def headers(self) -> List[Header]:
        return self._headers

    @property
    def content(self) -> List[Payload] | Payload:
        return self._content if len(self._content) > 1 else self._content[0]

class GmailService:

    _instance = None
    _lock = threading.Lock()
    _local = threading.local()

    def __new__(cls,*args,**kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(GmailService, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if not getattr(self,'_service') is None:
            return

    @property
    def _service(self):
        if not hasattr(self._local,'service'):
            self._credentials = AppConfig.get_config()._credentials
            self._local.service = build('gmail','v1',credentials=self._credentials)
        return self._local.service

    @classmethod
    def get_service(cls):
        if cls._instance is None:
            cls._instance = GmailService()
        return cls._instance

    def _get_mail_content(self,payload:dict):

        if 'parts' in payload:
            return [
                Payload(
                    part.get('partId',''),
                    part.get('mimeType',''),
                    part.get('filename',''),
                    part.get('headers',''),
                    part.get('body','')
                )
                for part in payload['parts']
            ]
        return [                
            Payload(
                    payload.get('partId',''),
                    payload.get('mimeType',''),
                    payload.get('filename',''),
                    payload.get('headers',''),
                    payload.get('body','')
                )
            ]

    def get_mails(self) -> Iterable[Mail]: # type: ignore
        mail_results = self._service.users().messages().list(
            userId='me',
            labelIds=['INBOX']
        ).execute()

        mails = mail_results.get('messages',[])

        for mail in mails:
            
            msg_id = mail['id']
            
            msg = self._service.users().messages().get(
                userId='me',
                id=msg_id,
                format='full'
            ).execute()
            
            mail = Mail(
                msg['id'],
                msg['threadId'],
                msg['labelIds'],
                msg['snippet'],
                msg['sizeEstimate'],
                msg['historyId'],
                msg['internalDate'],
                msg['payload'].get('headers',[]),
                self._get_mail_content(msg['payload'])
            )
            yield mail

class MailRepository:
    _lock = threading.Lock()
    _mails:Dict[str,Mail] = {}
    
    @classmethod
    def add(cls,*mails:Mail):
        with cls._lock:
            for mail in mails:
                cls._mails[mail.id] = mail

    @classmethod
    def get(cls,mail_id:str) -> Mail:
        with cls._lock:
            return cls._mails[mail_id]

    @classmethod
    def get_all(cls) -> List[Mail]:
        with cls._lock:
            return list(cls._mails.values())

    @classmethod
    def delete(cls,mail_id:str):
        with cls._lock:
            del cls._mails[mail_id]