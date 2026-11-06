"""Exercise actual MCP stdio handshake, schemas, calls, errors and recovery."""
import asyncio
import json
import sys
import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

CASES = [('castHexagram', {'method': 'manual', 'at': '2026-08-20T20:20:00', 'lines': [1, 1, 1, 1, 1, 1], 'moving': [1]}, {'method': 'manual', 'lines': [1, 1, 1, 1, 1, 1], 'moving': [7]})]

@pytest.mark.asyncio
async def test_stdio_protocol():
    async def scenario():
        params = StdioServerParameters(command=sys.executable, args=["-c", "from shunshi_liuyao_mcp.server import main; main()"])
        async with stdio_client(params) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                listed = await session.list_tools()
                assert {t.name for t in listed.tools} == {c[0] for c in CASES}
                for tool in listed.tools:
                    assert tool.description and tool.inputSchema["type"] == "object"
                for name, valid, invalid in CASES:
                    result = await session.call_tool(name, valid)
                    assert not result.isError, result
                    payload = json.loads(result.content[0].text)
                    assert payload["chart"]["ben"]["name"] == "乾为天"
                    assert payload["chart"]["bian"]["name"] == "天风姤"
                    error = await session.call_tool(name, invalid)
                    assert error.isError
                    again = await session.call_tool(name, valid)
                    assert not again.isError
    await asyncio.wait_for(scenario(), timeout=90)
