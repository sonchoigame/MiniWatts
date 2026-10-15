#!/usr/bin/env python3
import copy
import json
import pathlib
import re
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
CACHE_FILE = ROOT / ".vi-translation-cache.json"
CACHE_LOCK = Lock()

OVERRIDES = {
    "About": "Giới thiệu",
    "Accessories": "Phụ kiện",
    "Adapter": "Bộ sạc",
    "Battery": "Pin",
    "Battery Health": "Tình trạng pin",
    "Battery temperature": "Nhiệt độ pin",
    "Cable and connection": "Cáp và kết nối",
    "Cable comparison": "So sánh cáp",
    "Celsius": "Độ C",
    "Charging": "Đang sạc",
    "Charging history": "Lịch sử sạc",
    "Charging power": "Công suất sạc",
    "Current": "Dòng điện",
    "Current draw": "Dòng điện đang sử dụng",
    "Data": "Dữ liệu",
    "Discharging": "Đang xả pin",
    "Fahrenheit": "Độ F",
    "Get Reading": "Lấy số đo",
    "Input current": "Dòng điện đầu vào",
    "Input power": "Công suất đầu vào",
    "Input voltage": "Điện áp đầu vào",
    "Live Activity while charging": "Hoạt động trực tiếp khi sạc",
    "Lock Screen and widgets": "Màn hình khóa và tiện ích",
    "Lost in the path": "Tổn hao trên đường truyền",
    "Path resistance": "Điện trở đường truyền",
    "Power": "Công suất",
    "Reading": "Số đo",
    "Settings": "Cài đặt",
    "Taking": "Đang sử dụng",
    "Temperature": "Nhiệt độ",
    "Temperature unit": "Đơn vị nhiệt độ",
    "Throttled": "Bị giới hạn",
    "Time": "Thời gian",
    "Transport": "Kiểu kết nối",
    "Unavailable": "Không khả dụng",
    "unavailable": "không khả dụng",
    "Unit": "Đơn vị",
    "Unknown": "Không xác định",
    "Unknown adapter": "Bộ sạc không xác định",
    "Unknown device": "Thiết bị không xác định",
    "USB-C input": "Đầu vào USB-C",
    "USB-C input current": "Dòng điện đầu vào USB-C",
    "USB-C input voltage": "Điện áp đầu vào USB-C",
    "Voltage": "Điện áp",
    "Voltage drop": "Sụt áp",
    "Watts": "Công suất (W)",
    "Wired": "Có dây",
    "Wireless": "Không dây",
    "Wireless charger": "Bộ sạc không dây",
    "Wireless coil": "Cuộn sạc không dây",
    "Wireless input": "Đầu vào không dây",
    "Wireless input current": "Dòng điện đầu vào không dây",
    "Wireless input voltage": "Điện áp đầu vào không dây",
    "%lld sessions": "%lld phiên sạc",
    "%lld samples": "%lld mẫu đo",
    "%lld sensors": "%lld cảm biến",
    "%@ at the port": "%@ tại cổng sạc",
    "%@ hot": "Nóng %@",
    "%@ W in": "%@ W đầu vào",
    "%@ W to cell": "%@ W vào pin",
    "%lld%% of adapter": "%lld%% công suất bộ sạc",
    "at the current draw": "theo mức tiêu thụ hiện tại",
    "from one sample": "từ một mẫu đo",
    "fitted over the whole contract": "khớp theo toàn bộ cấu hình cấp nguồn",
    "of the current on offer": "dòng điện khả dụng",
    "W rated": "W định mức",
    "Get ${metric}": "Lấy ${metric}",
    "Get ${metric} in ${unit}": "Lấy ${metric} theo ${unit}",
}

PLACEHOLDER_RE = re.compile(r"(%(?:\d+\$)?[-+0 #]*\d*(?:\.\d+)?(?:hh|h|ll|l|L|z|t|j)?[@diuoxXfFeEgGaAcCsSp]|%%|\$\{[^}]+\})")

try:
    cache = json.loads(CACHE_FILE.read_text("utf-8")) if CACHE_FILE.exists() else {}
except Exception:
    cache = {}


def protect(text: str):
    placeholders = []
    def repl(m):
        token = f"ZXQPH{len(placeholders)}QXZ"
        placeholders.append((token, m.group(0)))
        return token
    return PLACEHOLDER_RE.sub(repl, text), placeholders


def restore(text: str, placeholders):
    for token, value in placeholders:
        text = text.replace(token, value)
        text = text.replace(token.lower(), value)
    return text


def google_translate(text: str) -> str:
    if not text.strip():
        return text
    if text in OVERRIDES:
        return OVERRIDES[text]
    with CACHE_LOCK:
        cached = cache.get(text)
    if cached is not None:
        return cached

    protected, placeholders = protect(text)
    params = urllib.parse.urlencode({
        "client": "gtx",
        "sl": "en",
        "tl": "vi",
        "dt": "t",
        "q": protected,
    })
    url = "https://translate.googleapis.com/translate_a/single?" + params
    last_error = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                payload = json.loads(r.read().decode("utf-8"))
            translated = "".join(part[0] for part in payload[0] if part and part[0])
            translated = restore(translated, placeholders)
            with CACHE_LOCK:
                cache[text] = translated
            return translated
        except Exception as exc:
            last_error = exc
            time.sleep(0.75 * (attempt + 1))
    raise RuntimeError(f"Không thể dịch chuỗi: {text!r}: {last_error}")


def walk_string_units(node):
    if isinstance(node, dict):
        if "stringUnit" in node and isinstance(node["stringUnit"], dict) and "value" in node["stringUnit"]:
            yield str(node["stringUnit"]["value"])
        for value in node.values():
            yield from walk_string_units(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk_string_units(value)


def collect_needed_texts(catalogs):
    needed = set()
    for path in catalogs:
        data = json.loads(path.read_text("utf-8"))
        for key, entry in data.get("strings", {}).items():
            if entry.get("shouldTranslate") is False:
                continue
            locs = entry.get("localizations", {})
            if "vi" in locs:
                continue
            if "en" in locs:
                needed.update(walk_string_units(locs["en"]))
            else:
                needed.add(key)
    return sorted(t for t in needed if t.strip() and t not in OVERRIDES and t not in cache)


def pretranslate(texts):
    if not texts:
        return
    print(f"[VI] Dịch song song {len(texts)} chuỗi...")
    done = 0
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = {pool.submit(google_translate, text): text for text in texts}
        for future in as_completed(futures):
            future.result()
            done += 1
            if done % 25 == 0 or done == len(texts):
                print(f"[VI] Đã dịch {done}/{len(texts)}")


def translate_node(node):
    if isinstance(node, dict):
        out = {}
        for k, v in node.items():
            if k == "stringUnit" and isinstance(v, dict) and "value" in v:
                unit = copy.deepcopy(v)
                unit["state"] = "translated"
                unit["value"] = google_translate(str(v["value"]))
                out[k] = unit
            else:
                out[k] = translate_node(v)
        return out
    if isinstance(node, list):
        return [translate_node(x) for x in node]
    return copy.deepcopy(node)


def localize_catalog(path: pathlib.Path):
    data = json.loads(path.read_text("utf-8"))
    count = 0
    skipped = 0
    for key, entry in data.get("strings", {}).items():
        if entry.get("shouldTranslate") is False:
            skipped += 1
            continue
        locs = entry.setdefault("localizations", {})
        if "vi" in locs:
            continue
        if "en" in locs:
            vi_node = translate_node(locs["en"])
        else:
            vi_node = {"stringUnit": {"state": "translated", "value": google_translate(key)}}
        locs["vi"] = vi_node
        count += 1

    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", "utf-8")
    print(f"[VI] {path.relative_to(ROOT)}: {count} chuỗi, bỏ qua {skipped} chuỗi kỹ thuật")
    return count


def main():
    catalogs = sorted(ROOT.rglob("Localizable.xcstrings"))
    if not catalogs:
        raise SystemExit("Không tìm thấy Localizable.xcstrings")
    pretranslate(collect_needed_texts(catalogs))
    total = sum(localize_catalog(path) for path in catalogs)
    CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n", "utf-8")
    print(f"[VI] Hoàn tất: {len(catalogs)} catalog, {total} mục tiếng Việt")


if __name__ == "__main__":
    main()
