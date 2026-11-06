"""Windows/minimal containers need bundled IANA data rather than OS zoneinfo."""
import zoneinfo
from shunshi_liuyao_mcp.server import castHexagram

def test_timezone_without_os_database():
    previous = zoneinfo.TZPATH
    try:
        zoneinfo.reset_tzpath(())
        zoneinfo.ZoneInfo.clear_cache()
        got = castHexagram(method="manual", timezone="Asia/Seoul", at="2026-08-20T20:20:00", lines=[1]*6, moving=[1])
        assert got["chart"]["ben"]["name"] == "乾为天"
        assert got["timezone"] == "Asia/Seoul"
    finally:
        zoneinfo.reset_tzpath(previous)
        zoneinfo.ZoneInfo.clear_cache()
