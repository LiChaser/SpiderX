import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp import FastMCP
from lichauto import LichAuto

mcp = FastMCP("lichauto")

@mcp.tool()
def auto_crack(urls: list[str]) -> dict:
    """
    对目标登录页面执行自动爆破，自动完成：目标分类→简单爆破→复杂爆破→返回凭证
    
    Args:
        urls: 目标登录页面的 URL 列表，如 ["http://example.com/login"]
    
    Returns:
        包含所有发现的账号密码的字典
    """
    lich = LichAuto()
    return lich.run(urls)

if __name__ == "__main__":
    mcp.run()
