from fastmcp import FastMCP
from tools.reddit import mcp as RedditToolsMCP
from tools.web import mcp as WebToolsMCP
from tools.drive import mcp as GoogleDriveMCP

mcp = FastMCP('MyTools')

mcp.mount(RedditToolsMCP)
mcp.mount(WebToolsMCP)
mcp.mount(GoogleDriveMCP)

mcp.run(transport='http',host='127.0.0.1',port=8000)