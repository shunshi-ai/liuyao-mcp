from datetime import datetime
from itertools import product
import pytest
from shunshi_liuyao import cast, build_gua, cast_coin

def test_reference_chart():
    gua = cast(method="manual", when=datetime(2026,8,20,20,20), lines=[1]*6, moving=[1])
    assert gua["sizhu"] == {"year":"丙午", "month":"丙申", "day":"丙寅", "hour":"戊戌", "month_zhi":"申", "kong_wang":"戌亥"}
    ben = gua["ben"]
    assert (ben["shi"], ben["ying"]) == (6,3)
    assert [y["ganzhi"] for y in ben["yao"]] == ["甲子","甲寅","甲辰","壬午","壬申","壬戌"]
    assert [y["liuqin"] for y in ben["yao"]] == ["子孙","妻财","父母","官鬼","兄弟","父母"]
    assert [y["liushen"] for y in ben["yao"]] == ["朱雀","勾陈","螣蛇","白虎","玄武","青龙"]
    assert gua["bian"]["name"] == "天风姤"

def test_all_hexagrams_and_single_changes():
    names = set()
    for lines in product((0,1), repeat=6):
        base = build_gua(list(lines), [], "丙寅", "申", "戌亥")
        names.add(base["ben"]["name"])
        for move in range(1,7):
            got = build_gua(list(lines), [move], "丙寅", "申", "戌亥")
            changed = list(lines)
            changed[move-1] ^= 1
            expected = build_gua(changed, [], "丙寅", "申", "戌亥")
            assert got["bian"]["name"] == expected["ben"]["name"]
            assert len(got["ben"]["yao"]) == 6
    assert len(names) == 64

@pytest.mark.parametrize("backs,expected,moves", [(0,0,True),(1,0,False),(2,1,False),(3,1,True)])
def test_coin_rule(backs, expected, moves):
    bits = iter(([1]*backs + [0]*(3-backs))*6)
    lines, moving = cast_coin(lambda: next(bits))
    assert lines == [expected]*6
    assert moving == (list(range(1,7)) if moves else [])
