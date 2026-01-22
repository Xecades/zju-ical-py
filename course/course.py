from abc import ABC, abstractmethod
from datetime import date, datetime, timedelta
from typing import Generic, TypeVar

from loguru import logger

from course.convert import dayOfWeekToWeekString, isEvenWeek, periodToTime
from ical.ical import Event
from utils.config import TermConfig, config
from utils.const import Term, TweakMethod, WeekType


def daterange(start: date, end: date):
    days = int((end - start).days)
    for n in range(days):
        yield start + timedelta(n)


class Course(ABC):
    weekType: WeekType
    start: int
    end: int
    teacher: str
    classId: str
    name: str
    location: str
    terms: list[Term]
    dayOfWeek: int
    credit: None | float

    @abstractmethod
    def __init__(self, raw: dict):
        pass

    def __repr__(self) -> str:
        res = "Course(\n"
        res += f"  name={self.name},\n"
        res += f"  weekType={self.weekType},\n"
        res += f"  dayOfWeek={self.dayOfWeek},\n"
        res += f"  start={self.start},\n"
        res += f"  end={self.end}\n"
        res += ")"
        return res

    def overlap(self, other: "Course") -> None | tuple[int, int]:
        """
        检查两个课程是否重叠，若重叠则返回重叠的起止节次
        """
        if self.classId != other.classId:
            return None
        if self.dayOfWeek != other.dayOfWeek:
            return None
        if self.weekType != other.weekType:
            return None
        if self.location != other.location:
            return None
        if self.teacher != other.teacher:
            return None

        if self.start > other.start:
            return other.overlap(self)

        if self.end < other.start:
            return None

        if self.start == other.start and self.end == other.end:
            logger.warning(
                f"发现重复课程: {self.name}, 时间: 星期{self.dayOfWeek} {self.start}-{self.end}"
            )

        return self.start, other.end

    def isInTerm(self, term: Term) -> bool:
        return term in self.terms

    def getStartDateTime(self, day: date) -> datetime:
        time = periodToTime(self.start)
        return datetime(day.year, day.month, day.day, time.hour, time.minute)

    def getEndDateTime(self, day: date) -> datetime:
        time = periodToTime(self.end - 1)
        dt = timedelta(minutes=45)
        return datetime(day.year, day.month, day.day, time.hour, time.minute) + dt

    def setTerms(self, termsStr: str) -> None:
        self.terms = []
        if "春" in termsStr:
            self.terms.append(Term.Spring)
        if "夏" in termsStr:
            self.terms.append(Term.Summer)
        if "秋" in termsStr:
            self.terms.append(Term.Autumn)
        if "冬" in termsStr:
            self.terms.append(Term.Winter)
        if any([x not in "春夏秋冬" for x in termsStr]):
            raise NotImplementedError(f"当前学期安排 {termsStr} 不在支持范围内，欢迎提交 PR")

    def printLog(self) -> None:
        weekString = dayOfWeekToWeekString(self.dayOfWeek)
        logger.info(f"{self.name}: {weekString} / {self.start}-{self.end - 1}")

    @abstractmethod
    def setWeekType(self, raw: str) -> None:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        res = f"教师: {self.teacher}"
        if self.credit is not None:
            res += f"\\n学分: {self.credit:.1f}"
        return res


T = TypeVar("T", bound="Course")


class CourseTable(ABC, Generic[T]):
    def __init__(self) -> None:
        self.courses: list[T] = []

    def __repr__(self) -> str:
        return str(self.courses)

    @abstractmethod
    def fromRes(self, res) -> None:
        pass

    def GetClassOfDay(self, day: int, term: Term) -> list[T]:
        res = []
        for course in self.courses:
            if course.dayOfWeek == day and course.isInTerm(term):
                res.append(course)
        return res

    def toEvents(self, termConfig: TermConfig) -> list[Event]:
        logger.info("开始生成课程表日历事件")

        try:
            termBegin = termConfig.Begin
            termEnd = termConfig.End

            oneDay = timedelta(days=1)

            shadowDates = {}
            modDescriptions = {}

            for d in daterange(termBegin, termEnd + oneDay):
                shadowDates[d] = d

            tweaks = config.tweaks
            for tweak in tweaks:
                if tweak.To < termBegin or tweak.From > termEnd:
                    continue
                if tweak.TweakType == TweakMethod.Clear:
                    for d in daterange(tweak.From, tweak.To + oneDay):
                        del shadowDates[d]
                elif tweak.TweakType == TweakMethod.Copy:
                    shadowDates[tweak.To] = tweak.From
                    modDescriptions[tweak.To] = tweak.Description
                elif tweak.TweakType == TweakMethod.Move:
                    shadowDates[tweak.To] = tweak.From
                    del shadowDates[tweak.From]
                    modDescriptions[tweak.From] = tweak.Description
                elif tweak.TweakType == TweakMethod.Exchange:
                    shadowDates[tweak.To] = tweak.From
                    shadowDates[tweak.From] = tweak.To
                    modDescriptions[tweak.To] = tweak.Description
                    modDescriptions[tweak.From] = tweak.Description
                elif tweak.TweakType == TweakMethod.Pending:
                    pass
                else:
                    raise ValueError(f"未知的调整类型: {tweak.TweakType}")

            classOfDay = {}
            for i in range(1, 8):
                classOfDay[i] = self.GetClassOfDay(i, termConfig.Term)

            termBeginDayOfWeek = termBegin.weekday() + 1
            mondayOfFirstWeek = (
                termBegin
                - timedelta(days=termBeginDayOfWeek - 1)
                - timedelta(weeks=termConfig.FirstWeekNo - 1)
            )

            events: list[Event] = []

            for actualDate, dateOfClass in shadowDates.items():
                classesOfCurrentDate = classOfDay[dateOfClass.weekday() + 1]
                isCurrentDateEvenWeek = isEvenWeek(mondayOfFirstWeek, dateOfClass)
                for course in classesOfCurrentDate:
                    if isCurrentDateEvenWeek and course.weekType == WeekType.OddOnly:
                        continue
                    if not isCurrentDateEvenWeek and course.weekType == WeekType.EvenOnly:
                        continue

                    description = course.description
                    if dateOfClass in modDescriptions:
                        description = modDescriptions[dateOfClass] + "\\n\\n" + description

                    events.append(
                        Event(
                            summary=course.name,
                            location=course.location,
                            description=description,
                            start=course.getStartDateTime(actualDate),
                            end=course.getEndDateTime(actualDate),
                        )
                    )
        except Exception as e:
            logger.error(f"课程表日历事件生成失败: {e}")
            raise e

        return events
