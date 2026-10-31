import re
from bs4 import BeautifulSoup
from urllib.parse import unquote
from typing import Callable, Iterable
from fastmcp import FastMCP

from services.v1 import GmailService,RedditService,MailRepository,RedditRepository
from services.v1.gmail import Mail

mcp = FastMCP('Reddit Tools')

@mcp.tool
async def get_reddit_emails():
    """gets the emails sended from Reddit"""

    mail_pattern = r'.*<noreply@redditmail\.com>'

    def filtby(iterable:Iterable[Mail],predicate:Callable[[Mail],bool]) -> Iterable[Mail]:
        for obj in iterable:
            if predicate(obj):
                yield obj
    
    def predicate(mail:Mail) -> bool:
        for header in mail.headers:
            if header.name.lower() == 'from' and re.fullmatch(mail_pattern,header.value):
                return True
        return False

    def get_mail_subject(mail:Mail) -> str:
        for header in mail.headers:
            if header.name.lower() == 'subject':
                return header.value
        return 'No Subject'
    
    try:
        service = GmailService.get_service()
        mails = filtby(service.get_mails(),predicate)
        MailRepository.add(*mails)
        resume = [f'Mail ID: {mail.id}\nMail Subject: {get_mail_subject(mail)}\n' for mail in MailRepository.get_all()]
        return '\n'.join(resume)
    except Exception as ex:
        return f"Error: {ex}"

def get_destination_link(href:str) -> str:
    if not href:
        return ''

    if 'click.redditmail.com/CL0/' in href:
        part = href.split("/CL0/", 1)[1]
        raw_link = part.split("/1/", 1)[0]
        return unquote(raw_link)

    return href

@mcp.tool
async def review_reddit_email(mail_id:str):
    """gets the content from a email by its id"""
    try:
        posts_links = []
        mail = MailRepository.get(mail_id)
        if isinstance(mail.content,list):
            for payload in mail.content:
                if payload.mime_type == 'text/html':
                    soup = BeautifulSoup(payload.body,'html.parser')
                    for a_tag in soup.find_all("a",href=True):
                        href:str = a_tag.get('href') # type: ignore
                        link = get_destination_link(href)
                        if not link:
                            continue
                        post_link = re.search(
                            r"https://www\.reddit\.com/r/[^/]+/comments/[^/?#]+/[^/?#]+",
                            link
                        )
                        if post_link:
                            posts_links.append(post_link.group(0))
        elif mail.content.mime_type == 'text/html':
            soup = BeautifulSoup(mail.content.body,'html.parser')
            for a_tag in soup.find_all("a",href=True):
                href:str = a_tag.get('href') # type: ignore
                link = get_destination_link(href)
                if link:
                    post_link = re.search(
                        r"https://www\.reddit\.com/r/[^/]+/comments/[^/?#]+/[^/?#]+",
                        link
                    )
                    if post_link:
                        posts_links.append(post_link.group(0))
        posts_links = list(dict.fromkeys(posts_links))
        return 'Links\n' + '\n'.join(posts_links)
    except Exception as ex:
        return f'Error: {ex}'

@mcp.tool
async def review_post_url(post_url:str):
    """gets all the necesary information about the post of the given url"""
    try:
        service = RedditService.get_service()
        post_data,comments = service.get_post_data(post_url)
        if not post_data.is_deleted_or_removed:
            RedditRepository.add_post(post_data)
            for comment in comments:
                RedditRepository.add_comment_to_post(post_data.result_id,comment)
            text = ''
            text += f'Title: {post_data.title}\nAuthor: {post_data.author}\n'
            text += f'Post ID: {post_data.result_id}\n'
            text += f'Score: {post_data.score}\n'
            text += f'Upvoute ratio: {post_data.upvote_ratio}\n'
            text += f'Comments per hour: {post_data.comments_per_hour}\n\n'
            return text
        return 'Post deleted' 
    except Exception as ex:
        return f'Error: {ex}'

@mcp.tool
async def get_post_content(post_id:str):
    """gets the content of the post with the given id"""
    try:
        post = RedditRepository.get_post(post_id)
        if post:
            return post.body_html
        return 'the post doesn\'t exists'
    except Exception as ex:
        return f'Error: {ex}'

@mcp.tool
async def get_post_comments(post_id:str):
    """gets the comments of the post with the given id"""
    try:
        comments = [
            f'Score: {comment.score}\nContent: {comment.body_html}\nAuthor: {comment.author}'
            for comment in RedditRepository.get_all_post_comments(post_id)
        ]
        return '\n\n'.join(comments)
    except Exception as ex:
        return f'Error: {ex}'