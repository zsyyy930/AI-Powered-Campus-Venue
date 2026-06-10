"""从 自习空间调研表.xlsx 生成 knowledge/ 下的自习空间 Markdown 文件。"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
XLSX = ROOT / "自习空间调研表.xlsx"
OUT_DIR = ROOT / "knowledge"

COL = {
    "building": 0,
    "floor": 1,
    "area": 2,
    "comfort": 4,
    "outlet": 5,
    "lamp": 6,
    "hours24": 7,
    "noise": 8,
    "water": 9,
    "canteen": 10,
    "yuhu": 11,
    "ac": 12,
    "booking": 13,
    "note": 14,
}

SKIP_AREA_PATTERNS = (
    r"^注：",
    r"^建议提前",
)

SKIP_BUILDING_PATTERNS = (
    r"^注：",
    r"^建议提前",
)

INHERIT_KEYS = (
    "comfort",
    "outlet",
    "lamp",
    "hours24",
    "noise",
    "water",
    "canteen",
    "yuhu",
    "ac",
    "booking",
    "note",
)

BUILDING_NOTES: dict[str, list[str]] = {
    "主馆": ["有静音仓，二楼为 24 小时开放"],
    "基础馆": ["三楼信息共享空间不定期举办沙龙讲座"],
    "农医馆": [
        "建议提前预约；农医馆经常较空，很多人默认先来后到；"
        "若未预约就坐，图助通常会提醒补预约（可先找空位再预约）",
    ],
    "北教": ["很多教室上课兼自习，使用前注意查看教室外的课程表"],
}

LIBRARY_BUILDINGS = frozenset({"方闻馆", "古籍馆", "主馆", "农医馆", "基础馆"})
LIBRARY_HOLIDAY_NOTE = (
    "寒暑假期间部分图书馆可能闭馆或调整开放时间，"
    "请关注「浙大图书馆」微信公众号获取最新通知。"
)


def resolve_opening_hours(building: str, floor: str | None, area: str | None = None) -> str | None:
    """按浙大图书馆公布的各馆区开放时间返回说明文字。"""
    if building not in LIBRARY_BUILDINGS:
        return None

    fl = (floor or "").strip()
    ar = (area or "").strip()

    if building == "主馆":
        if fl in ("一楼", "二楼") or "刷夜" in ar:
            return "一、二楼全天开放（24 小时）"
        if fl in ("三楼", "四楼", "五楼", "六楼"):
            return "8:30–22:30（三至六楼）"
        return "一、二楼全天开放（24 小时）；三至六楼 8:30–22:30"

    if building == "基础馆":
        return (
            "8:30–22:30（大厅咨询台、自助借书仪，书库 1、书库 2、东亚文献阅览室等）；"
            "民国文献阅览室 8:30–17:30（仅工作日）；"
            "浙大文库 8:30–12:00、13:30–17:30（仅工作日）"
        )

    if building == "古籍馆":
        if fl == "一楼":
            return (
                "8:30–22:00（咨询台、自助借书仪、大厅展厅）；"
                "古籍阅览室 8:30–12:00、13:30–17:30（仅工作日）"
            )
        if fl in ("二楼", "三楼"):
            return "8:30–22:00（二层、三层书库与阅览室）"
        return (
            "8:30–22:00（咨询台、自助借书仪、大厅展厅）；"
            "古籍阅览室 8:30–12:00、13:30–17:30（仅工作日）；"
            "二层、三层书库与阅览室 8:30–22:00"
        )

    if building == "方闻馆":
        return (
            "8:30–22:30（东阅览室、西阅览室）；"
            "珍本阅览室、三层密集书库 8:30–12:00、13:30–17:30（仅工作日）"
        )

    if building == "农医馆":
        return (
            "8:30–22:30（其余区域）；"
            "文献传递 8:30–12:00、13:30–17:30（仅工作日）"
        )

    return None


def _cell(row, key) -> str | None:
    val = row.iloc[COL[key]]
    if pd.isna(val):
        return None
    s = str(val).strip()
    return s if s else None


def _format_outlet(raw: str | None) -> str | None:
    if not raw:
        return None
    try:
        n = float(raw)
        if 0 <= n <= 1:
            return f"覆盖率约 {int(round(n * 100))}%"
    except ValueError:
        pass
    return raw


def _inherit_row(row, prev: pd.Series | None) -> pd.Series:
    if prev is None:
        return row
    merged = row.copy()
    area = _cell(row, "area") or ""
    for key in INHERIT_KEYS:
        if _cell(merged, key) is None and _cell(prev, key) is not None:
            merged.iloc[COL[key]] = str(prev.iloc[COL[key]])
    if area == "同上" and _cell(prev, "area"):
        merged.iloc[COL["area"]] = _cell(prev, "area")
    elif area == "同一、二楼":
        merged.iloc[COL["area"]] = "一至二楼通用自习区（各层布局相近）"
    return merged


def _should_skip(building: str, area: str) -> bool:
    if not area or not area.strip():
        return True
    for pat in SKIP_BUILDING_PATTERNS:
        if re.search(pat, building):
            return True
    for pat in SKIP_AREA_PATTERNS:
        if re.search(pat, area):
            return True
    if area in ("具体区域", "nan"):
        return True
    return False


def _safe_filename(parts: list[str]) -> str:
    raw = "-".join(p for p in parts if p)
    raw = re.sub(r'[\\/:*?"<>|=\s]+', "-", raw)
    raw = re.sub(r"-+", "-", raw).strip("-")
    if len(raw) > 80:
        raw = raw[:80].rstrip("-")
    return f"自习-{raw}.md"


def _title(building: str, floor: str | None, area: str) -> str:
    bits = [building]
    if floor:
        bits.append(floor)
    bits.append(area)
    return "".join(bits)


def _build_md(
    building: str,
    floor: str | None,
    area: str,
    row: pd.Series,
    extra_notes: list[str],
) -> str:
    title = _title(building, floor, area)
    lines = [f"# {title}", ""]

    lines += ["## 位置与区域", ""]
    lines.append(f"- **建筑**：{building}")
    if floor:
        lines.append(f"- **楼层**：{floor}")
    lines.append(f"- **具体区域**：{area}")
    lines.append("- **类型**：自习空间")
    lines.append("")

    lines += ["## 设施与环境", ""]
    facility_items = [
        ("座椅舒适度", _cell(row, "comfort"), lambda v: f"{v} / 5 星"),
        ("插座", _format_outlet(_cell(row, "outlet")), None),
        ("单独台灯", _cell(row, "lamp"), None),
        ("空调暖气", _cell(row, "ac"), None),
        ("噪音水平", _cell(row, "noise"), None),
        ("饮用水", _cell(row, "water"), None),
    ]
    for label, val, fmt in facility_items:
        if val:
            text = fmt(val) if fmt else val
            lines.append(f"- **{label}**：{text}")
    lines.append("")

    lines += ["## 开放与预约", ""]
    hours = resolve_opening_hours(building, floor, area)
    if hours:
        lines.append(f"- **开放时间**：{hours}")
    h24 = _cell(row, "hours24")
    if h24:
        lines.append(f"- **24 小时开放**：{h24}")
    booking = _cell(row, "booking")
    if booking:
        lines.append(f"- **是否需预约**：{booking}")
    canteen = _cell(row, "canteen")
    if canteen:
        lines.append(f"- **距食堂**：{canteen}")
    yuhu = _cell(row, "yuhu")
    if yuhu:
        lines.append(f"- **距玉湖宿舍**：{yuhu}")
    lines.append("")

    note = _cell(row, "note")
    if note or extra_notes:
        lines += ["## 备注", ""]
        if note:
            lines.append(f"- {note}")
        for n in extra_notes:
            lines.append(f"- {n}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def load_rows() -> list[tuple[str, str | None, str, pd.Series]]:
    df = pd.read_excel(XLSX, sheet_name=0, header=1)
    df.iloc[:, COL["building"]] = df.iloc[:, COL["building"]].ffill()
    df.iloc[:, COL["floor"]] = df.iloc[:, COL["floor"]].ffill()

    rows: list[tuple[str, str | None, str, pd.Series]] = []
    prev: pd.Series | None = None
    for _, raw_row in df.iterrows():
        building = _cell(raw_row, "building") or ""
        floor = _cell(raw_row, "floor")
        area = _cell(raw_row, "area") or ""
        if not building or building == "建筑":
            continue
        if _should_skip(building, area):
            prev = raw_row
            continue
        merged = _inherit_row(raw_row, prev)
        prev = merged
        rows.append((building, floor, area, merged))
    return rows


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    count = 0
    for building, floor, area, row in load_rows():
        display_area = _cell(row, "area") or area
        extra = list(BUILDING_NOTES.get(building, []))
        if building in LIBRARY_BUILDINGS:
            extra.append(LIBRARY_HOLIDAY_NOTE)
        md = _build_md(building, floor, display_area, row, extra)
        fname = _safe_filename([building, floor or "", display_area])
        (OUT_DIR / fname).write_text(md, encoding="utf-8")
        count += 1
        print(f"  {fname}")
    print(f"\n共生成 {count} 个文件 → {OUT_DIR}")


if __name__ == "__main__":
    main()
