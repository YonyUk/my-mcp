import threading
from typing import Dict, Tuple
from apify_client import ApifyClient

from config import AppConfig, List

class ApifyResult:

    def __init__(
        self,
        result_id:str,
        kind:str,
        body:str,
        author:str,
        score:int = 0,
        subreddit:str = '',
        created_utc:str = '',
        score_per_hour:float = 0.0,
        is_deleted_or_removed:bool = False,
        author_fullname:str = '',
        body_html:str = ''
    ):
        self._result_id:str = result_id
        self._kind:str = kind
        self._body:str = body
        self._author:str = author
        self._score:int = score
        self._subreddit:str = subreddit
        self._created_utc:str = created_utc
        self._score_per_hour:float = score_per_hour
        self._is_deleted_or_removed:bool = is_deleted_or_removed
        self._author_fullname:str = author_fullname
        self._body_html:str = body_html

    @property
    def result_id(self) -> str:
        return self._result_id

    @property
    def kind(self) -> str:
        return self._kind

    @property
    def body(self) -> str:
        return self._body

    @property
    def author(self) -> str:
        return self._author

    @property
    def score(self) -> int:
        return self._score

    @property
    def subreddit(self) -> str:
        return self._subreddit

    @property
    def created_utc(self) -> str:
        return self._created_utc

    @property
    def score_per_hour(self) -> float:
        return self._score_per_hour

    @property
    def is_deleted_or_removed(self) -> bool:
        return self._is_deleted_or_removed

    @property
    def author_fullname(self) -> str:
        return self._author_fullname

    @property
    def body_html(self) -> str:
        return self._body_html

class PostApifyResult(ApifyResult):

    def __init__(
        self,
        post_id: str,
        title: str = '',
        body: str = '',
        author: str = '',
        score: int = 0,
        upvote_ratio: float = 0.0,
        num_comments: int = 0,
        subreddit: str = '',
        created_utc: str = '',
        has_media: bool = False,
        score_per_hour: float = 0.0,
        comments_per_hour: float = 0.0,
        is_deleted_or_removed: bool = False,
        engagement_total: int = 0,
        comment_to_score_ratio: float = 0.0,
        author_fullname: str = '',
        body_html: str = '',
        *args,
        **kwargs
    ):
        super().__init__(
            post_id,
            "post",
            body,
            author,
            score,
            subreddit,
            created_utc,
            score_per_hour,
            is_deleted_or_removed,
            author_fullname,
            body_html
        )

        self._title:str = title
        self._upvote_ratio:float = upvote_ratio
        self._num_comments = num_comments
        self._comments_per_hour:float = comments_per_hour
        self._comment_to_score_ratio:float = comment_to_score_ratio
        self._engagement_total:int = engagement_total
        self._has_media:bool = has_media

    @property
    def title(self) -> str:
        return self._title

    @property
    def upvote_ratio(self) -> float:
        return self._upvote_ratio
    
    @property
    def has_media(self) -> bool:
        return self._has_media
    
    @property
    def num_comments(self) -> int:
        return self._num_comments

    @property
    def comments_per_hour(self) -> float:
        return self._comments_per_hour
    
    @property
    def comment_to_score_ratio(self) -> float:
        return self._comment_to_score_ratio

    @property
    def engagement_total(self) -> int:
        return self._engagement_total

class CommentApifyResult(ApifyResult):

    def __init__(
        self,
        comment_id:str,
        post_id:str,
        body:str = '',
        author:str = '',
        score:int = 0,
        subreddit:str = '',
        created_utc:str = '',
        is_deleted_or_removed:bool = False,
        score_per_hour:float = 0.0,
        author_fullname:str = '',
        body_html:str = '',
        *args,
        **kwargs
    ):
        super().__init__(
            comment_id,
            "comment",
            body,
            author,
            score,
            subreddit,
            created_utc,
            score_per_hour,
            is_deleted_or_removed,
            author_fullname,
            body_html
        )

        self._post_id:str = post_id

    @property
    def post_id(self) -> str:
        return self._post_id

class RedditRepository:

    _posts:Dict[str,PostApifyResult] = {}
    _comments:Dict[str,Dict[str,CommentApifyResult]] = {}
    _lock = threading.Lock()

    @classmethod
    def add_post(cls,post:PostApifyResult):
        with cls._lock:
            cls._posts[post.result_id] = post

    @classmethod
    def add_comment_to_post(cls,post_id:str,comment:CommentApifyResult):
        with cls._lock:
            cls._comments.setdefault(post_id,{})[comment.result_id] = comment

    @classmethod
    def get_post(cls,post_id:str) -> PostApifyResult | None:
        with cls._lock:
            return cls._posts.get(post_id,None)

    @classmethod
    def get_post_comment(cls,post_id:str,comment_id:str) -> CommentApifyResult | None:
        with cls._lock:
            return cls._comments.get(post_id,{}).get(comment_id,None)

    @classmethod
    def get_all_posts(cls) -> List[PostApifyResult]:
        with cls._lock:
            return list(cls._posts.values())

    @classmethod
    def get_all_post_comments(cls,post_id:str) -> List[CommentApifyResult]:
        with cls._lock:
            return list(cls._comments.get(post_id,{}).values())

    @classmethod
    def delete_post(cls,post_id:str):
        with cls._lock:
            del cls._posts[post_id]

    @classmethod
    def delete_post_comment(cls,post_id:str,comment_id:str):
        with cls._lock:
            del cls._comments[post_id][comment_id]

class RedditService:

    _instance = None
    _lock = threading.Lock()

    def __new__(cls,*args,**kargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(RedditService,cls).__new__(cls)
        return cls._instance

    @classmethod
    def get_service(cls):
        if not cls._instance:
            cls._instance = RedditService()
        return cls._instance

    def __init__(self) -> None:
        if not getattr(self,'_service') is None:
            return
        config = AppConfig.get_config()
        token = config.apify_api_token
        self._actor_id = config.apify_actor_id
        self._client = ApifyClient(token)

    def _normalize_comment(self, raw: dict) -> dict:
        return {
            'comment_id': raw.get('id', ''),
            'post_id': raw.get('postId', ''),
            'body': raw.get('body', ''),
            'author': raw.get('author', ''),
            'score': raw.get('score', 0) or 0,
            'subreddit': raw.get('subreddit', ''),
            'created_utc': raw.get('createdUtc', raw.get('created_utc', '')),
            'is_deleted_or_removed': raw.get('isDeletedOrRemoved',
                                              raw.get('is_deleted_or_removed', False)),
            'score_per_hour': raw.get('scorePerHour',
                                      raw.get('score_per_hour', 0.0)) or 0.0,
            'author_fullname': raw.get('authorFullname',
                                       raw.get('author_fullname', '')),
            'body_html': raw.get('bodyHtml', raw.get('body_html', '')),
        }

    def _normalize_post(self, raw: dict) -> dict:
        return {
            'post_id': raw.get('id', ''),
            'title': raw.get('title', ''),
            'body': raw.get('body', ''),
            'author': raw.get('author', ''),
            'score': raw.get('score', 0) or 0,
            'upvote_ratio': raw.get('upvoteRatio', raw.get('upvote_ratio', 0.0)) or 0.0,
            'num_comments': raw.get('numComments', raw.get('num_comments', 0)) or 0,
            'subreddit': raw.get('subreddit', ''),
            'created_utc': raw.get('createdUtc', raw.get('created_utc', '')),
            'has_media': raw.get('hasMedia', raw.get('has_media', False)),
            'score_per_hour': raw.get('scorePerHour',
                                      raw.get('score_per_hour', 0.0)) or 0.0,
            'comments_per_hour': raw.get('commentsPerHour',
                                         raw.get('comments_per_hour', 0.0)) or 0.0,
            'is_deleted_or_removed': raw.get('isDeletedOrRemoved',
                                              raw.get('is_deleted_or_removed', False)),
            'engagement_total': raw.get('engagementTotal',
                                        raw.get('engagement_total', 0)) or 0,
            'comment_to_score_ratio': raw.get('commentToScoreRatio',
                                              raw.get('comment_to_score_ratio', 0.0)) or 0.0,
            'author_fullname': raw.get('authorFullname',
                                       raw.get('author_fullname', '')),
            'body_html': raw.get('bodyHtml', raw.get('body_html', '')),
        }

    def get_post_data(self,url:str) -> Tuple[PostApifyResult,List[CommentApifyResult]]:
        run_input = {
            "urls": [
                url
            ],
            "scrapeComments":True,
            "scrapeUpvotes":True,
            "maxComments":100
        }

        run = self._client.actor(self._actor_id).call(run_input=run_input)
        dataset_id = run.default_dataset_id # type: ignore
        raw_results = self._client.dataset(dataset_id).iterate_items()
        post_result:PostApifyResult = None # type: ignore
        comments_result:List[CommentApifyResult] = []
        for raw_result in raw_results:
            if raw_result['kind'] == 'post':
                post_result = PostApifyResult(**self._normalize_post(raw_result))
            else:
                comments_result.append(CommentApifyResult(**self._normalize_comment(raw_result)))

        return post_result,comments_result