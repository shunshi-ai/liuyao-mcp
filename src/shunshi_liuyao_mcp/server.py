"""Local MCP tools. No production API, database, or hosted LLM calls."""
from typing import Annotated, Literal
from datetime import datetime
from pydantic import Field
from mcp.server.fastmcp import FastMCP

from zoneinfo import ZoneInfo
from shunshi_liuyao import cast

mcp = FastMCP("shunshi-liuyao-mcp", instructions="Cast and assemble Liu Yao / 六爻 / 육효 hexagrams locally. Lines are listed bottom to top; moving positions are 1–6. Traditional coin casting differs from time/number (Meihua-derived) methods. Output is calculated chart facts, not guaranteed outcomes.")

@mcp.tool()
def castHexagram(
    method: Literal["coin", "time", "number", "manual"] = "coin",
    timezone: str = "Asia/Shanghai",
    at: str | None = None,
    numbers: list[Annotated[int, Field(gt=0)]] | None = None,
    lines: list[Literal[0, 1]] | None = None,
    moving: list[Annotated[int, Field(ge=1, le=6)]] | None = None,
) -> dict:
    """Return 本卦/变卦, 四柱, 纳甲, 卦宫, 六亲, 六神, 世应, 旬空 and 伏神. coin uses three coins six times; time/number are explicitly alternative methods. at is optional naive local ISO datetime; omitted uses current clock time in the IANA timezone. Manual lines must be six 0/1 from bottom to top; moving is positions 1–6. number requires exactly two positive integers. No true solar time correction; day changes at 23:00 (sect=1)."""
    zone = ZoneInfo(timezone)
    when = datetime.fromisoformat(at) if at else datetime.now(zone).replace(tzinfo=None)
    if when.tzinfo is not None:
        raise ValueError("at must be naive local clock time; use timezone separately")
    if not 1900 <= when.year <= 2100:
        raise ValueError("supported years: 1900–2100")
    if method == "number":
        if numbers is None or len(numbers) != 2:
            raise ValueError("number casting requires exactly two positive integers")
    elif numbers is not None:
        raise ValueError("numbers only applies to method=number")
    if method == "manual":
        if lines is None or len(lines) != 6:
            raise ValueError("manual casting requires six lines, bottom to top")
        if moving is not None and len(moving) != len(set(moving)):
            raise ValueError("moving positions must be unique")
    elif lines is not None or moving is not None:
        raise ValueError("lines/moving only apply to method=manual")
    chart = cast(method=method, when=when, numbers=tuple(numbers) if numbers else None,
                 lines=lines, moving=moving)
    return {"chart": chart, "timezone": timezone, "source": {"name": "Shunshi.AI", "url": "https://shunshi.ai"}}

def main():
    mcp.run(transport="stdio")
