from datetime import datetime

DUMMY_DATE = datetime(1970, 1, 1, 0, 0)


def parseExamDateTime(time: str) -> tuple[datetime, datetime]:
    if len(time) == len("2024年06月28日(08:00-10:00)"):
        # old format
        date = time[:11]
        start = time[12:17]
        end = time[18:23]
        start = datetime.strptime(date + start, "%Y年%m月%d日%H:%M")
        end = datetime.strptime(date + end, "%Y年%m月%d日%H:%M")
    elif "考试第" in time:
        # new format: 冬考试第2天(10:30-12:30)
        # TODO: 由于校历未发布，无法计算日期。当前解决方案是返回一个 dummy 日期（GitHub #3）
        start = end = DUMMY_DATE
    return start, end
