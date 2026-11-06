from __future__ import annotations
import json
import re
import threading
from functools import lru_cache as _lru_cache
from datetime import date, datetime
from pathlib import Path
_DATA_DIR = Path(__file__).resolve().parent / 'data'
_lock = threading.Lock()
_najia: dict | None = None
_bagua: dict | None = None
_gua64: dict | None = None
_bagong: dict | None = None
_lines_index: dict | None = None
TIAN_GAN = '甲乙丙丁戊己庚辛壬癸'
DI_ZHI = '子丑寅卯辰巳午未申酉戌亥'
ZHI_WUXING = {'子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火', '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水'}
_LIUSHEN_ORDER = ['青龙', '朱雀', '勾陈', '螣蛇', '白虎', '玄武']
_LIUSHEN_START = {'甲': 0, '乙': 0, '丙': 1, '丁': 1, '戊': 2, '己': 3, '庚': 4, '辛': 4, '壬': 5, '癸': 5}
_SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
_KE = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}
_SHI_FLIP = {'本宫': [], '一世': [1], '二世': [1, 2], '三世': [1, 2, 3], '四世': [1, 2, 3, 4], '五世': [1, 2, 3, 4, 5], '游魂': [1, 2, 3, 5], '归魂': [5]}
_SHI_POS = {'本宫': 6, '一世': 1, '二世': 2, '三世': 3, '四世': 4, '五世': 5, '游魂': 4, '归魂': 3}
_PALACES = ['乾', '坎', '艮', '震', '巽', '离', '坤', '兑']

def _ensure_loaded() -> None:
    global _najia, _bagua, _gua64, _lines_index, _bagong
    if _najia is not None:
        return
    with _lock:
        if _najia is not None:
            return

        def _load(name: str) -> dict:
            raw = json.load(open(_DATA_DIR / name, encoding='utf-8'))
            return {k: v for (k, v) in raw.items() if not k.startswith('_')}
        (najia, bagua, gua64) = (_load('najia.json'), _load('bagua.json'), _load('gua64.json'))
        lines_index = {v['lines']: k for (k, v) in bagua.items()}
        bagong = _build_bagong(bagua, gua64, lines_index)
        (_najia, _bagua, _gua64) = (najia, bagua, gua64)
        (_lines_index, _bagong) = (lines_index, bagong)

def _build_bagong(bagua: dict, gua64: dict, lines_index: dict) -> dict:
    """推导京房八宫表 → {卦名: {palace, shi_name, shi, ying}}。

    自校验：必须无重复地覆盖全部 64 卦，否则规则写错了，直接抛。
    """
    table: dict = {}
    for palace in _PALACES:
        tri = bagua[palace]['lines']
        base = [int(c) for c in tri] * 2
        for (shi_name, flips) in _SHI_FLIP.items():
            six = base[:]
            for pos in flips:
                six[pos - 1] ^= 1
            name = _name_of(six, gua64, lines_index)
            if name in table:
                raise RuntimeError(f"八宫推导撞车: {name} 同时属 {table[name]['palace']}宫{table[name]['shi_name']} 与 {palace}宫{shi_name}")
            shi = _SHI_POS[shi_name]
            table[name] = {'palace': palace, 'palace_wuxing': bagua[palace]['wuxing'], 'shi_name': shi_name, 'shi': shi, 'ying': shi + 3 if shi + 3 <= 6 else shi - 3}
    missing = set(gua64.values()) - set(table)
    if missing:
        raise RuntimeError(f'八宫推导缺卦: {sorted(missing)}')
    return table

def _name_of(six: list, gua64: dict, lines_index: dict) -> str:
    """六爻(index0=初爻) → 卦名。key 是「上卦下卦」。"""
    lower = ''.join((str(x) for x in six[:3]))
    upper = ''.join((str(x) for x in six[3:]))
    return gua64[lines_index[upper] + lines_index[lower]]

def _liuqin(palace_wx: str, yao_wx: str) -> str:
    """六亲：以卦宫五行为「我」。"""
    if yao_wx == palace_wx:
        return '兄弟'
    if _SHENG[yao_wx] == palace_wx:
        return '父母'
    if _SHENG[palace_wx] == yao_wx:
        return '子孙'
    if _KE[yao_wx] == palace_wx:
        return '官鬼'
    return '妻财'

def _liushen(day_gan: str) -> list:
    """六神，返回 index0=初爻 → index5=上爻。"""
    start = _LIUSHEN_START[day_gan]
    return [_LIUSHEN_ORDER[(start + i) % 6] for i in range(6)]

def _najia_pillars(six: list) -> list:
    """纳甲：六爻 → 六个干支，index0=初爻。内卦纳一干、外卦纳一干。"""
    _ensure_loaded()
    lower = _lines_index[''.join((str(x) for x in six[:3]))]
    upper = _lines_index[''.join((str(x) for x in six[3:]))]
    (lo, up) = (_najia[lower], _najia[upper])
    return [lo['gan_inner'] + z for z in lo['inner']] + [up['gan_outer'] + z for z in up['outer']]

def _chong(zhi: str) -> str:
    """地支相冲：相隔六位。"""
    return DI_ZHI[(DI_ZHI.index(zhi) + 6) % 12]

def _facts(zhi: str, day_zhi: str, month_zhi: str, kong_wang: str, skip_kong: bool=False) -> dict:
    """一个地支相对起卦时刻的可核对事实。全是事实，一条判断都没有。

    skip_kong=True 用于变卦爻：**旬空只作用于本卦和伏神，变爻不论空**。
    这里给 None（不适用）而不是 False（算过了、不空）—— 后者是句假话，
    早晚有人读到它当成「变爻不空」去断事。
    月建日辰那几项变爻仍然要算：回头生克得看变爻自身旺不旺。
    """
    return {'kong': None if skip_kong else zhi in kong_wang, 'de_yue': zhi == month_zhi, 'yue_po': zhi == _chong(month_zhi), 'ri_chong': zhi == _chong(day_zhi), 'lin_ri': zhi == day_zhi}

def _fu_shen(palace: str, ben_yao: list, day_ganzhi: str, month_zhi: str, kong_wang: str) -> dict:
    """伏神：本卦不上卦的六亲，去**本宫首卦（纯卦）的同爻位**取。

    为什么必须有这个：64 卦里只有 20 卦（31%）六亲五种全齐。
    妻财不上卦的有 16 卦、子孙不上卦的有 16 卦 —— 也就是说**每四个问财的
    卦就有一个用神根本不在盘面上**。没有伏神，解读层到这里就无爻可引，
    模型只能开始编（这正是「经过一番磨难」那类空话的来源之一）。

    取法（《增删卜易》通行）：把本宫纯卦六爻按爻位一一对应下来，
    纯卦那一爻的六亲若在本卦中缺席，它就伏在本卦同爻位之下，
    压着它的那个本卦爻叫「飞神」。

    本来担心一个歧义：八纯卦里有的六亲占两爻（如乾宫父母在初、上两爻），
    缺的若正好是它，按爻位对应会两爻都挂伏神、解读层不知道该引哪个。
    64 卦全量实测下来**这情况一次都不发生** —— 缺失六亲共 56 例，
    伏神爻恰好也是 56 个，一一对应。所以这里不需要任何挑选规则。

    返回 {爻位(1-indexed): 伏神 dict}，只覆盖有伏神的爻位。
    """
    _ensure_loaded()
    palace_wx = _bagua[palace]['wuxing']
    pure = [int(c) for c in _bagua[palace]['lines']] * 2
    day_zhi = day_ganzhi[1]
    present = {y['liuqin'] for y in ben_yao}
    out: dict = {}
    for (i, gz) in enumerate(_najia_pillars(pure)):
        wx = ZHI_WUXING[gz[1]]
        lq = _liuqin(palace_wx, wx)
        if lq in present:
            continue
        fei = ben_yao[i]
        out[i + 1] = {'pos': i + 1, 'ganzhi': gz, 'wuxing': wx, 'liuqin': lq, 'fei_ganzhi': fei['ganzhi'], 'fei_liuqin': fei['liuqin'], **_facts(gz[1], day_zhi, month_zhi, kong_wang)}
    return out

def build_gua(lines: list, moving: list, day_ganzhi: str, month_zhi: str, kong_wang: str) -> dict:
    """装卦。

    lines:       六个 0/1，index0=初爻（0=阴 1=阳）
    moving:      动爻位置列表，1-indexed（老阴老阳的位置）
    day_ganzhi:  起卦日干支，如 "丙寅"
    month_zhi:   起卦月支（月建），如 "申"
    kong_wang:   日柱旬空两支，如 "戌亥"

    返回 {"ben": {...}, "bian": {...} | None}。
    只给盘面事实，不给吉凶。
    """
    _ensure_loaded()
    if len(lines) != 6 or any((x not in (0, 1) for x in lines)):
        raise ValueError('lines 必须是 6 个 0/1，index0=初爻')
    ben = _assemble(lines, moving, day_ganzhi, month_zhi, kong_wang)
    fu = _fu_shen(ben['palace'], ben['yao'], day_ganzhi, month_zhi, kong_wang)
    ben['fu_shen'] = fu
    for y in ben['yao']:
        y['fu'] = fu.get(y['pos'])
    bian = None
    if moving:
        changed = lines[:]
        for pos in moving:
            changed[pos - 1] ^= 1
        bian = _assemble(changed, [], day_ganzhi, month_zhi, kong_wang, palace_override=ben['palace_wuxing'], is_bian=True)
        bian['moving_from'] = list(moving)
    return {'ben': ben, 'bian': bian}

def _assemble(six: list, moving: list, day_ganzhi: str, month_zhi: str, kong_wang: str, palace_override: str | None=None, is_bian: bool=False) -> dict:
    name = _name_of(six, _gua64, _lines_index)
    info = _bagong[name]
    palace_wx = palace_override or info['palace_wuxing']
    pillars = _najia_pillars(six)
    shens = _liushen(day_ganzhi[0])
    day_zhi = day_ganzhi[1]
    yao = []
    for i in range(6):
        gz = pillars[i]
        zhi = gz[1]
        wx = ZHI_WUXING[zhi]
        pos = i + 1
        yao.append({'pos': pos, 'yin_yang': '阳' if six[i] else '阴', 'moving': pos in moving, 'ganzhi': gz, 'wuxing': wx, 'liuqin': _liuqin(palace_wx, wx), 'liushen': shens[i], 'shi_ying': '世' if pos == info['shi'] else '应' if pos == info['ying'] else '', **_facts(zhi, day_zhi, month_zhi, kong_wang, skip_kong=is_bian)})
    return {'name': name, 'palace': info['palace'], 'palace_wuxing': info['palace_wuxing'], 'shi_name': info['shi_name'], 'shi': info['shi'], 'ying': info['ying'], 'yao': yao}
_XIANTIAN = {1: '乾', 2: '兑', 3: '离', 4: '震', 5: '巽', 6: '坎', 7: '艮', 8: '坤'}
CAST_METHODS = ('coin', 'time', 'number', 'manual')

def _lines_from_trigrams(upper: str, lower: str) -> list:
    """上卦+下卦 → 六爻，index0=初爻。下卦在初二三，上卦在四五上。"""
    _ensure_loaded()
    return [int(c) for c in _bagua[lower]['lines']] + [int(c) for c in _bagua[upper]['lines']]

def cast_coin(rng=None) -> tuple:
    """摇钱币：三枚一掷，掷六次。这是六爻的**正法**，另外两种是变通。

    背为阳、字为阴，按背的个数定：
      3 背 = 老阳（阳，动）  2 背 = 少阳（阳，静）
      1 背 = 少阴（阴，静）  0 背 = 老阴（阴，动）
    所以老阳/老阴各 1/8、少阳/少阴各 3/8 —— 这个不对称是真的，
    别图省事写成「每爻 50% 阴阳 + 独立 20% 动」，那会把动爻概率整体拉高。

    用 secrets 不用 random：起卦结果是用户唯一无法验证的一步，
    至少保证它不是可预测的伪随机序列。
    """
    import secrets
    rand = rng or (lambda : secrets.randbelow(2))
    (lines, moving) = ([], [])
    for pos in range(1, 7):
        backs = sum((rand() for _ in range(3)))
        lines.append(1 if backs >= 2 else 0)
        if backs in (0, 3):
            moving.append(pos)
    return (lines, moving)

def cast_time(when: datetime) -> tuple:
    """时间起卦（梅花法）：农历年支数+月+日 定上卦，再加时辰数定下卦。

    上卦 =（年支序 + 农历月 + 农历日）% 8，余 0 作 8
    下卦 =（上面三个 + 时支序）% 8，余 0 作 8
    动爻 =（同四数之和）% 6，余 0 作 6 —— 时间起卦**只出一个动爻**。
    """
    from lunar_python import Solar
    lunar = Solar.fromDate(when).getLunar()
    year_i = DI_ZHI.index(lunar.getYearZhi()) + 1
    month_i = abs(lunar.getMonth())
    day_i = lunar.getDay()
    hour_i = DI_ZHI.index(lunar.getTimeZhi()) + 1
    base = year_i + month_i + day_i
    upper = _XIANTIAN[base % 8 or 8]
    lower = _XIANTIAN[(base + hour_i) % 8 or 8]
    move = (base + hour_i) % 6 or 6
    return (_lines_from_trigrams(upper, lower), [move])

def cast_number(n1: int, n2: int) -> tuple:
    """数字起卦：两个数分别定上下卦，和定动爻。同样只出一个动爻。"""
    if n1 <= 0 or n2 <= 0:
        raise ValueError('起卦数字必须为正整数')
    upper = _XIANTIAN[n1 % 8 or 8]
    lower = _XIANTIAN[n2 % 8 or 8]
    return (_lines_from_trigrams(upper, lower), [(n1 + n2) % 6 or 6])
_LOCALE_TZ = {'ko': 'Asia/Seoul', 'ja': 'Asia/Tokyo', 'zh-cn': 'Asia/Shanghai', 'zh-tw': 'Asia/Taipei'}

def cast(method: str='coin', when: datetime | None=None, numbers: tuple | None=None, question: str | None=None, lines: list | None=None, moving: list | None=None) -> dict:
    """Cast and assemble a hexagram using local clock time; sect=1 and no solar correction."""
    from .calendar import calc_bazi, get_kong_wang
    if method not in CAST_METHODS:
        raise ValueError(f'未知起卦方式 {method!r}，只支持 {CAST_METHODS}')
    when = when or datetime.now()
    sizhu = calc_bazi(when, 1)['四柱'].split()
    (day_gz, month_zhi) = (sizhu[2], sizhu[1][1])
    kong = get_kong_wang(day_gz)
    if method == 'coin':
        (lines, moving) = cast_coin()
    elif method == 'time':
        (lines, moving) = cast_time(when)
    elif method == 'number':
        if not numbers or len(numbers) != 2:
            raise ValueError('number 起卦需要两个数字')
        (lines, moving) = cast_number(*numbers)
    else:
        if not lines:
            raise ValueError('manual 起卦需要 lines（六个 0/1，index0=初爻）')
        moving = sorted(set(moving or []))
        if any((p not in range(1, 7) for p in moving)):
            raise ValueError('动爻位置只能是 1-6')
    gua = build_gua(lines, moving, day_gz, month_zhi, kong)
    gua['cast'] = {'method': method, 'at': when.isoformat(timespec='seconds'), 'question': question, 'lines': lines, 'moving': moving}
    gua['sizhu'] = {'year': sizhu[0], 'month': sizhu[1], 'day': sizhu[2], 'hour': sizhu[3], 'month_zhi': month_zhi, 'kong_wang': kong}
    return gua
