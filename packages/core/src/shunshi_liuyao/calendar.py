"""Minimal public lunar-python adapter. Same sect=1 primitives as production."""
from lunar_python import Solar
from lunar_python.util import LunarUtil

def calc_bazi(when, gender):
    ec = Solar(when.year, when.month, when.day, when.hour, when.minute, when.second).getLunar().getEightChar()
    ec.setSect(1)
    return {"四柱": " ".join((ec.getYear(), ec.getMonth(), ec.getDay(), ec.getTime()))}

def get_kong_wang(gz):
    stems, branches = "甲乙丙丁戊己庚辛壬癸", "子丑寅卯辰巳午未申酉戌亥"
    index = (branches.index(gz[1]) - stems.index(gz[0])) % 12
    return LunarUtil.XUN_KONG[{0: 0, 10: 1, 8: 2, 6: 3, 4: 4, 2: 5}[index]]
