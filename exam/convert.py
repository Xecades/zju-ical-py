from datetime import datetime


def parseExamDateTime(time: str) -> tuple[datetime, datetime]:
    assert len(time) == len("2024年06月28日(08:00-10:00)"), "时间格式错误"
    date = time[:11]
    start = time[12:17]
    end = time[18:23]
    start = datetime.strptime(date + start, "%Y年%m月%d日%H:%M")
    end = datetime.strptime(date + end, "%Y年%m月%d日%H:%M")
    return start, end
