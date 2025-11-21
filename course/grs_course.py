from loguru import logger
from course.convert import dayOfWeekToWeekString
from course.course import Course, CourseTable
from utils.const import WeekType


class GRSCourse(Course):
    termInfo: str = ""
    courseType: str = ""
    comment: str = ""
    school: str = ""

    def __init__(self, raw: dict):
        self.credit = None
        self.classId = raw["bjbh"][:7]  # 班级编号
        self.dayOfWeek = int(raw["xqj"])  # 星期几

        # 学期
        pkxqMc: str = raw["pkxqMc"]  # 排课学期名称
        self.setTerms(pkxqMc)

        self.setWeekType(raw["zc"])  # 周次

        self.name = raw["kcmc"]  # 课程名称
        self.teacher = raw["xm"]  # 姓名
        self.location = raw["cdmc"] if raw["cdmc"] else ""  # 场地名称

        self.start = int(raw["ksjc"])  # 开始节次
        self.end = int(raw["jsjc"]) + 1  # 结束节次

        self.printLog()

    def setWeekType(self, raw: str) -> None:
        week_list = [int(w) for w in raw.split(",") if w] if raw else []

        # 设置单双周标志
        threshold = 8 if len(self.terms) > 1 else 4
        if len(week_list) > threshold:
            self.weekType = WeekType.Normal
        else:
            odd_week_count = sum(1 for w in week_list if w % 2 == 1)
            if odd_week_count > len(week_list) / 2:
                self.weekType = WeekType.OddOnly
            else:
                self.weekType = WeekType.EvenOnly

    @property
    def description(self) -> str:
        res = super().description
        res += f"\\n课号: {self.classId}"
        res += f"\\n课程类型: {self.courseType}"
        res += f"\\n学期: {self.termInfo}"
        res += f"\\n时间: {dayOfWeekToWeekString(self.dayOfWeek)}"
        if self.start == self.end - 1:
            res += f" 第{self.start}节"
        else:
            res += f" 第{self.start}-{self.end - 1}节"
        res += f"\\n开课学院: {self.school}"
        res += f"\\n备注: {self.comment}"
        return res


class GRSCourseTable(CourseTable):
    courses: list[GRSCourse]

    def fromRes(self, res: dict) -> None:
        for day in range(1, 7):
            if str(day) not in res:
                continue
            classesOfDay = res[str(day)]
            for period in range(1, 15):
                if str(period) not in classesOfDay:
                    continue
                classesOfPeriod = classesOfDay[str(period)]["pyKcbjSjddVOList"]
                for raw in classesOfPeriod:
                    if "," not in raw["zc"]:
                        continue  # 跳过因为调休而单列的课程
                    c = GRSCourse(raw)
                    self.courses.append(c)

    def grsGetInfo(self, res: list[dict]) -> None:
        for course in self.courses:
            for r in res:
                if r.get("kcbh") == course.classId:
                    course.credit = float(r.get("xf", 0))
                    course.courseType = r.get("kcxzDm") if r.get(
                        "kcxzDm") else ""  # 课程性质代码
                    course.courseType += ("(" + r.get("bx") +
                                          ")") if r.get("bx") else ""  # 必选修
                    course.comment = r.get("bz") if r.get("bz") else ""  # 备注
                    course.school = r.get("kkxyMc") if r.get(
                        "kkxyMc") else ""  # 开课学院名称
                    if course.location == "" and any(x in course.comment for x in ["线上", "录播", "直播"]):
                        course.location = "线上"
                    courseInfo = r.get("sjddBz") if r.get(
                        "sjddBz") else ""  # 时间地点备注
                    course.termInfo = courseInfo.split("<br/>")[0]

                    break

    def deDup(self) -> None:
        logger.info("研究生：开始去重课程表")
        try:
            uniqueCourses = {}
            for course in self.courses:
                key = (course.classId, course.dayOfWeek, course.start,
                       course.end, course.location, course.teacher)
                if key not in uniqueCourses:
                    uniqueCourses[key] = course
            self.courses = list(uniqueCourses.values())
        except Exception as e:
            logger.error(f"研究生：课程表去重失败: {e}")
            raise e
