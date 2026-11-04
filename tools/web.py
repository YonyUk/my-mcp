import webless
import urllib.request as ur
import asyncio
from fastmcp import FastMCP,Context
from mcp.server.session import ServerSession

mcp = FastMCP('Web Tools')

async def open_browser(url:str,ctx:Context):
    result = await asyncio.wait_for(
        ctx.session.elicit_url(
            message=f'Open {url} directly in your browser?',
            url=url,
            elicitation_id='open-url-001'
        ),
        timeout=10.0
    )
    return result

@mcp.tool
def review_url(url:str):
    """open the given url and gets its content in HTML format"""
    try:
        return ur.urlopen(url).read()
    except Exception as ex:
        return f'Error: {ex}'

@mcp.tool
def search_in_web(subject:str):
    """gets info from web about the given subject"""
    try:
        results = asyncio.run(webless.search(subject)).hits
        text_results = [
            f'Title: {hit.title}\nSnippet: {hit.snippet}\nScore: {hit.score}\nURL: {hit.url}'
            for hit in results
        ]
        return ('-'*50 + '\n').join(text_results)
    except Exception as ex:
        return f'Error: {ex}'

@mcp.tool
def open_url_in_browser(url:str,ctx:Context):
    """open the given url in the client browser"""
    try:
        result = asyncio.run(open_browser(url,ctx))
        if result.action == 'accept':
            return f'The user accepted to open the url'
        elif result.action == "decline":
            return "The user refused to open the url"
        return "The user cancelled the request"
    except Exception as ex:
        return f'Error: {ex}'