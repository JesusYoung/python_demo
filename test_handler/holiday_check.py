import json
import ssl
from urllib import request
from datetime import datetime, timedelta


def _fetch_holiday_mmdd_for_year(year):
    url = f"https://timor.tech/api/holiday/year/{year}"
    try:
        ctx = ssl._create_unverified_context()
        with request.urlopen(url, context=ctx, timeout=8) as resp:
            if resp.getcode() != 200:
                return set()
            data = json.load(resp)
            if data.get("code") != 0:
                return set()
            holiday_dict = data.get("holiday", {})
            festival_mmdd = set()
            for mmdd, info in holiday_dict.items():
                if not isinstance(info, dict):
                    continue
                is_holiday = info.get("holiday", False)
                name = info.get("name", "")
                is_spring_festival = "春节" in name or "除夕" in name
                is_national_day = "国庆" in name
                if is_holiday and (is_spring_festival or is_national_day):
                    parts = mmdd.split("-")
                    if len(parts) == 2:
                        m = parts[0].zfill(2)
                        d = parts[1].zfill(2)
                        festival_mmdd.add(f"{m}-{d}")
            return festival_mmdd
    except Exception:
        return set()


def _get_date_range(start_str, end_str):
    try:
        start = datetime.strptime(start_str, "%Y-%m-%d")
        end = datetime.strptime(end_str, "%Y-%m-%d")
        if start > end:
            return []
        current = start
        dates = []
        while current <= end:
            dates.append(current)
            current += timedelta(days=1)
        return dates
    except ValueError:
        return []


def main(arg1):
    try:
        records = json.loads(arg1)
    except json.JSONDecodeError:
        return {"result": {"error": "Invalid JSON format"}}

    valid_special_cases = {"国家法定长假日", "境外"}
    rejection_messages = []

    for record in records:
        line_num = record.get("lineNum", "").strip()
        start_str = record.get("startTime", "").strip()
        end_str = record.get("endTime", "").strip()
        special_case = record.get("specialCase", "").strip()

        if not start_str or not end_str:
            continue

        date_objects = _get_date_range(start_str, end_str)
        if not date_objects:
            continue

        years = {d.strftime("%Y") for d in date_objects}
        year_to_festival_mmdd = {}
        for year in years:
            mmdd_set = _fetch_holiday_mmdd_for_year(year)
            year_to_festival_mmdd[year] = mmdd_set

        has_festival = False
        for dt in date_objects:
            year = dt.strftime("%Y")
            mmdd = dt.strftime("%m-%d")
            if mmdd in year_to_festival_mmdd.get(year, set()):
                has_festival = True
                break

        if has_festival:
            if special_case not in valid_special_cases:
                msg = f"出差日期含国家法定长假日，请在特殊情况字段选择“国家法定长假日”"
                rejection_messages.append(msg)

    if rejection_messages:
        return {"result": {"驳回信息": rejection_messages}}
    else:
        return {"result": {"res": "通过"}}


# ====== 调试用的测试入口 ======
if __name__ == "__main__":
    # 构造测试输入（与你实际调用格式一致）
    test_input = [
        {
            "lineNum": "1",
            "busiCate": "日常性出差",
            "specialCase": "否",
            "from": "深圳",
            "to": "西安",
            "startTime": "2025-10-01",
            "endTime": "2025-10-01"
        }
    ]

    # 转为 JSON 字符串（模拟外部传入）
    arg1 = json.dumps(test_input, ensure_ascii=False)

    # 调用主函数
    result = main(arg1)

    # 打印结果（美化输出）
    print("校验结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))