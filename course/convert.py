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


def dayOfWeekToWeekString(day: int) -> None | str:
    if day == 1:
        return "星期一"
    elif day == 2:
        return "星期二"
    elif day == 3:
        return "星期三"
    elif day == 4:
        return "星期四"
    elif day == 5:
        return "星期五"
    elif day == 6:
        return "星期六"
    elif day == 7:
        return "星期日"
    return None


def ugrsClassTermToQueryString(term: Term) -> None | str:
    if term == Term.Autumn:
        return "1|秋"
    elif term == Term.Winter:
        return "1|冬"
    elif term == Term.ShortA:
        return "1|短"
    elif term == Term.SummerVacation:
        return "1|暑"
    elif term == Term.Spring:
        return "2|春"
    elif term == Term.Summer:
        return "2|夏"
    elif term == Term.ShortB:
        return "2|短"
    return None


def periodToTime(period: int) -> None | Time:
    if period == 1:
        return Time(8, 0)
    elif period == 2:
        return Time(8, 50)
    elif period == 3:
        return Time(10, 0)
    elif period == 4:
        return Time(10, 50)
    elif period == 5:
        return Time(11, 40)
    elif period == 6:
        return Time(13, 25)
    elif period == 7:
        return Time(14, 15)
    elif period == 8:
        return Time(15, 5)
    elif period == 9:
        return Time(16, 15)
    elif period == 10:
        return Time(17, 5)
    elif period == 11:
        return Time(18, 50)
    elif period == 12:
        return Time(19, 40)
    elif period == 13:
        return Time(20, 30)
    elif period == 14:
        return Time(21, 20)
    elif period == 15:
        return Time(22, 10)
    return None
