import webless
import webbrowser
import urllib.request as ur
from fastmcp import FastMCP

mcp = FastMCP('Web Tools')

@mcp.tool
async def review_url(url:str):
    """open the given url and gets its content in HTML format"""
    try:
        return ur.urlopen(url).read()
    except Exception as ex:
        return f'Error: {ex}'

@mcp.tool
async def search_in_web(subject:str):
    """gets info from web about the given subject"""
    try:
        results = (await webless.search(subject)).hits
        text_results = [
            f'Title: {hit.title}\nSnippet: {hit.snippet}\nScore: {hit.score}\nURL: {hit.url}'
            for hit in results
        ]
        return ('-'*50 + '\n').join(text_results)
    except Exception as ex:
        return f'Error: {ex}'

@mcp.tool
async def open_url_in_browser(url:str):
    """open the given url in the browser"""
    try:
        opened = webbrowser.open(url)
        return f'url {url} successfully opened' if opened else 'browser not opened'
    except Exception as ex:
        return f'Error: {ex}'