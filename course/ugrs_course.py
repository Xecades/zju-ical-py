from loguru import logger
from course.course import Course, CourseTable
from utils.const import WeekType


class UGRSCourse(Course):
    timeString: str

    def __init__(self, raw: dict):
        self.credit = None
        # 不确定为什么要截取前22位，但Celechron是这样做的
        self.classId = raw["xkkh"][:22]  # 选课课号
        self.dayOfWeek = int(raw["xqj"])  # 星期几

        self.setWeekType(raw["dsz"])  # 单双周

        # 课程表
        kcb = raw["kcb"]
        kcb = kcb.split("zwf")[0].split("<br>")
        self.name = kcb[0].replace("(", "（").replace(")", "）")
        self.timeString = kcb[1]
        self.teacher = kcb[2]
        self.location = None if kcb[3] == "" else kcb[3]

        # 学期
        xxq: str = raw["xxq"]
        self.setTerms(xxq)

        self.start = int(raw["djj"])  # 第几节
        self.end = self.start + int(raw["skcd"])  # 上课长度

        self.printLog()

    def setWeekType(self, raw: str) -> None:
        # 单双周
        if raw == "0":
            self.weekType = WeekType.OddOnly
        elif raw == "1":
            self.weekType = WeekType.EvenOnly
        else:
            self.weekType = WeekType.Normal

    @property
    def description(self) -> str:
        res = super().description
        res += "\\n" + self.timeString + " "

        if self.start == self.end - 1:
            res += f"第{self.start}节"
        else:
            res += f"第{self.start}-{self.end - 1}节"
        return res


class UGRSCourseTable(CourseTable):
    courses: list[UGRSCourse]

    def fromRes(self, res: list[dict]) -> None:
        for raw in res:
            c = UGRSCourse(raw)
            self.courses.append(c)

    def communicate(self, exams: "ExamTable") -> None:
        for course in self.courses:
            examsOfCourse = exams.find(course)
            if len(examsOfCourse) == 0:
                continue
            course.credit = examsOfCourse[0].credit

    def merge(self) -> None:
        logger.info("本科生：开始相连时段课程表合并")
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
            logger.error(f"本科生：课程表合并失败: {e}")
            raise e
