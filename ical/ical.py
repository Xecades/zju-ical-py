from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha1

from loguru import logger

from course.convert import toISOString


@dataclass
class Event:
    summary: str
    location: str
    description: str
    start: datetime
    end: datetime | None = None

    @property
    def uid(self) -> str:
        m = sha1()
        m.update(self.description.encode())
        m.update(self.summary.encode())
        m.update(self.location.encode())
        m.update(toISOString(self.start).encode())
        return m.hexdigest()

    @property
    def string(self) -> str:
        utcStr = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        stStr = toISOString(self.start)

        res = f"BEGIN:VEVENT\r\nCLASS:PUBLIC\r\nCREATED:{utcStr}\r\n"
        if self.description:
            if "=0D=0A" in self.description:
                res += f"DESCRIPTION;ENCODING=QUOTED-PRINTABLE:{self.description}\r\n"
            else:
                res += f"DESCRIPTION:{self.description}\r\n"
        res += f"DTSTAMP:{utcStr}\r\n"
        res += f"DTSTART;TZID=Asia/Shanghai:{stStr}\r\n"
        if self.end:
            etStr = toISOString(self.end)
            res += f"DTEND;TZID=Asia/Shanghai:{etStr}\r\n"

        res += f"LAST-MODIFIED:{utcStr}\r\n"
        if self.location:
            res += f"LOCATION:{self.location}\r\n"
        res += f"SEQUENCE:0\r\nSUMMARY;LANGUAGE=zh-cn:{self.summary}\r\nTRANSP:OPAQUE\r\nUID:{self.uid}\r\n"
        res += "END:VEVENT\r\n"
        return res


class Calender:
    events: list[Event]

    def __init__(self):
        self.events = []

    def add(self, **kwargs) -> None:
        self.events.append(Event(**kwargs))

    def addEvents(self, events: list[Event]) -> None:
        self.events.extend(events)

    def getICS(self, icalName: str = "ZJU-ICAL 课程表") -> str:
        logger.info("开始生成日历文件")
        res = f"BEGIN:VCALENDAR\r\nX-WR-CALNAME:{icalName}\r\nX-APPLE-CALENDAR-COLOR:#2BBFF0\r\nPRODID:-//ZJU-ICAL-PY//Ejector 0.2//EN\r\nVERSION:2.0\r\nMETHOD:PUBLISH\r\nBEGIN:VTIMEZONE\r\nTZID:Asia/Shanghai\r\nBEGIN:STANDARD\r\nDTSTART:16010101T000000\r\nTZOFFSETFROM:+0800\r\nTZOFFSETTO:+0800\r\nEND:STANDARD\r\nEND:VTIMEZONE\r\n"
        for event in self.events:
            res += event.string
        res += "END:VCALENDAR\r\n"
        return res
