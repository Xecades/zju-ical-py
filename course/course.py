from utils.const import Term, WeekType, TweakMethod
from utils.config import config, TermConfig
from loguru import logger
from datetime import date, datetime, timedelta
from course.convert import isEvenWeek, periodToTime, dayOfWeekToWeekString
from ical.ical import Event


def daterange(start: date, end: date):
    days = int((end - start).days)
    for n in range(days):
        yield start + timedelta(n)


class Course:
    SCHEME_ZDBK = "ZDBK"

    weekType: WeekType
    start: int
    end: int
    teacher: str
    classId: str
    name: str
    location: str
    terms: list[Term]
    timeString: str
    dayOfWeek: int
    credit: None | float

    def __init__(self, raw: dict, scheme: str):
        if scheme != Course.SCHEME_ZDBK:
            raise NotImplementedError("不支持的课程查询方案")

        self.credit = None
        # 不确定为什么要截取前22位，但Celechron是这样做的
        self.classId = raw["xkkh"][:22]  # 选课课号
        self.dayOfWeek = int(raw["xqj"])  # 星期几

        # 单双周
        if raw["dsz"] == "0":
            self.weekType = WeekType.OddOnly
        elif raw["dsz"] == "1":
            self.weekType = WeekType.EvenOnly
        else:
            self.weekType = WeekType.Normal

        # 课程表
        kcb = raw["kcb"]
        kcb = kcb.split("zwf")[0].split("<br>")
        self.name = kcb[0].replace("(", "（").replace(")", "）")
        self.timeString = kcb[1]
        self.teacher = kcb[2]
        self.location = None if kcb[3] == "" else kcb[3]

        # 学期
        xxq: str = raw["xxq"]
        self.terms = []
        if "春" in xxq:
            self.terms.append(Term.Spring)
        if "夏" in xxq:
            self.terms.append(Term.Summer)
        if "秋" in xxq:
            self.terms.append(Term.Autumn)
        if "冬" in xxq:
            self.terms.append(Term.Winter)
        if any([x not in "春夏秋冬" for x in xxq]):
            raise NotImplementedError(f"当前学期安排 {xxq} 不在支持范围内，欢迎提交 PR")

        self.start = int(raw["djj"])  # 第几节
        self.end = self.start + int(raw["skcd"])  # 上课长度

        weekString = dayOfWeekToWeekString(self.dayOfWeek)
        logger.info(f"{self.name}: {weekString} / {self.start}-{self.end - 1}")

    def __repr__(self) -> str:
        res = "Course(\n"
        res += f"  name={self.name},\n"
        res += f"  weekType={self.weekType},\n"
        res += f"  dayOfWeek={self.dayOfWeek},\n"
        res += f"  start={self.start},\n"
        res += f"  end={self.end}\n"
        res += ")"
        return res

    def overlap(self, other: "Course") -> bool | tuple[int, int]:
        if self.classId != other.classId:
            return False
        if self.dayOfWeek != other.dayOfWeek:
            return False
        if self.weekType != other.weekType:
            return False

        if self.start > other.start:
            return other.overlap(self)

        if self.end < other.start:
            return False

        assert self.end == other.start, "相同课程不应该发生重叠，请联系开发者"
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

    @property
    def arrangementString(self) -> str:
        res = self.timeString + " "

        if self.start == self.end - 1:
            res += f"第{self.start}节"
        else:
            res += f"第{self.start}-{self.end - 1}节"
        return res


class CourseTable:
    courses: list[Course]

    def __init__(self):
        self.courses: list[Course] = []

    def __repr__(self) -> str:
        return str(self.courses)

    def fromZdbk(self, res: list[dict]) -> None:
        for raw in res:
            c = Course(raw, Course.SCHEME_ZDBK)
            self.courses.append(c)

    def communicate(self, exams: "ExamTable") -> None:
        for course in self.courses:
            examsOfCourse = exams.find(course)
            if len(examsOfCourse) == 0:
                continue
            course.credit = examsOfCourse[0].credit

    def merge(self) -> None:
        logger.info("开始相连时段课程表合并")
        try:
            for i in range(len(self.courses)):
                if self.courses[i] is None:
                    continue
                for j in range(i + 1, len(self.courses)):
                    if self.courses[j] is None:
                        continue

                    if overlap := self.courses[i].overlap(self.courses[j]):
                        start, end = overlap
                        self.courses[i].start = start
                        self.courses[i].end = end
                        self.courses[j] = None
            self.courses = list(filter(lambda c: c is not None, self.courses))
        except Exception as e:
            logger.error(f"课程表合并失败: {e}")
            raise e

    def GetClassOfDay(self, day: int, term: int) -> list[Course]:
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
                    modDescriptions[tweak.To] = tweak.Description
                elif tweak.TweakType == TweakMethod.Exchange:
                    shadowDates[tweak.To] = tweak.From
                    shadowDates[tweak.From] = tweak.To
                    modDescriptions[tweak.To] = tweak.Description
                    modDescriptions[tweak.From] = tweak.Description
                else:
                    raise ValueError(f"未知的调整类型: {tweak.TweakType}")

            classOfDay = {}
            for i in range(1, 8):
                classOfDay[i] = self.GetClassOfDay(i, termConfig.Term)

            termBeginDayOfWeek = termBegin.weekday() + 1
            mondayOfFirstWeek = termBegin - \
                timedelta(days=termBeginDayOfWeek - 1) - \
                timedelta(weeks=termConfig.FirstWeekNo - 1)

            events: list[Event] = []

            for actualDate, dateOfClass in shadowDates.items():
                classesOfCurrentDate = classOfDay[dateOfClass.weekday() + 1]
                isCurrentDateEvenWeek = isEvenWeek(
                    mondayOfFirstWeek, dateOfClass)
                for course in classesOfCurrentDate:
                    if isCurrentDateEvenWeek and course.weekType == WeekType.OddOnly:
                        continue
                    if not isCurrentDateEvenWeek and course.weekType == WeekType.EvenOnly:
                        continue

                    description = f"教师: {course.teacher}"
                    if course.credit is not None:
                        description += "\\n学分: %.1f" % course.credit
                    description += f"\\n{course.arrangementString}"
                    if dateOfClass in modDescriptions:
                        description = modDescriptions[dateOfClass] + \
                            "\\n\\n" + description

                    events.append(Event(
                        summary=course.name,
                        location=course.location,
                        description=description,
                        start=course.getStartDateTime(actualDate),
                        end=course.getEndDateTime(actualDate)
                    ))
        except Exception as e:
            logger.error(f"课程表日历事件生成失败: {e}")
            raise e

        return events
