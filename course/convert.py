from collections import namedtuple
from datetime import date, datetime

from utils.const import Term

Time = namedtuple("Time", ["hour", "minute"])


def toISOString(date: date) -> str:
    return date.strftime("%Y%m%dT%H%M%S")


def isoToDate(iso: int) -> datetime:
    return datetime.fromisoformat(str(iso))


def isEvenWeek(mondayOfTermBegin: date, date: date) -> bool:
    return (date - mondayOfTermBegin).days // 7 % 2 == 1


def dayOfWeekToWeekString(day: int) -> str:
    mapping = {
        1: "星期一",
        2: "星期二",
        3: "星期三",
        4: "星期四",
        5: "星期五",
        6: "星期六",
        7: "星期日",
    }
    if day not in mapping:
        raise ValueError(f"未知的星期数: {day}")
    return mapping[day]


def ugrsClassTermToQueryString(term: Term) -> str:
    mapping = {
        Term.Autumn: "1|秋",
        Term.Winter: "1|冬",
        Term.ShortA: "1|短",
        Term.SummerVacation: "1|暑",
        Term.Spring: "2|春",
        Term.Summer: "2|夏",
        Term.ShortB: "2|短",
    }
    if term not in mapping:
        raise ValueError(f"未知的学期: {term.value}")
    return mapping[term]


def grsGetYear(year: str, term: Term) -> str:
    years = year.split("-")
    if term == Term.Autumn or term == Term.Winter:
        return years[0]
    elif term == Term.Spring or term == Term.Summer:
        return years[1]
    raise ValueError(f"学年参数错误，无法从[{year}-{term.value}]中获取正确学年")


def grsClassTermToQueryString(term: Term) -> str:
    mapping = {
        Term.Autumn: "13",
        Term.Winter: "14",
        Term.Spring: "11",
        Term.Summer: "12",
    }
    if term not in mapping:
        raise ValueError(f"未知的学期: {term.value}")
    return mapping[term]


def periodToTime(period: int) -> Time:
    mapping = {
        1: Time(8, 0),
        2: Time(8, 50),
        3: Time(10, 0),
        4: Time(10, 50),
        5: Time(11, 40),
        6: Time(13, 25),
        7: Time(14, 15),
        8: Time(15, 5),
        9: Time(16, 15),
        10: Time(17, 5),
        11: Time(18, 50),
        12: Time(19, 40),
        13: Time(20, 30),
        14: Time(21, 20),
        15: Time(22, 10),
    }
    if period not in mapping:
        raise ValueError(f"未知的节次: {period}")
    return mapping[period]
