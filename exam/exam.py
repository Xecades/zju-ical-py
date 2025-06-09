from datetime import datetime
from utils.const import ExamType
from exam.convert import parseExamDateTime, DUMMY_DATE
from ical.ical import Event
from utils.logger import getLogger
from course.course import Course, CourseTable

log = getLogger(__name__)


class Exam:
    SCHEME_ZDBK = "ZDBK"

    classId: str
    name: str
    credit: float
    examType: ExamType
    start: None | datetime
    end: None | datetime
    location: None | str
    seat: None | str

    isEventGenerated: bool

    def __init__(self, raw: dict, scheme: str, examType: ExamType):
        if scheme != Exam.SCHEME_ZDBK:
            raise NotImplementedError("不支持的考试查询方案")

        self.isEventGenerated = False

        self.examType = examType
        self.classId = raw["xkkh"][:22]  # 选课课号
        self.name = raw["kcmc"].replace("(", "（").replace(")", "）")  # 课程名称
        self.credit = float(raw["xf"])  # 学分

        if examType == ExamType.FinalTerm:
            self.start, self.end = parseExamDateTime(raw["kssj"])  # 考试时间
            self.location = raw.get("jsmc", None)  # 教室名称
            self.seat = raw.get("zwxh", None)  # 座位序号
        elif examType == ExamType.MidTerm:
            self.start, self.end = parseExamDateTime(raw["qzkssj"])  # 期中考试时间
            self.location = raw.get("qzjsmc", None)  # 期中教室名称
            self.seat = raw.get("qzzwxh", None)
        else:
            self.start = None
            self.end = None
            self.location = None
            self.seat = None

        if self.start == self.end == DUMMY_DATE:
            log.info(
                f"{self.examType.value}: {self.name} {self.classId} (考试时间获取失败，可能是由于校历未发布无法计算时间，通常不影响当前学期日历，请参见 GitHub #3)")
        log.info(f"{self.examType.value}: {self.name} {self.classId}")

    def __repr__(self) -> str:
        res = "Exam(\n"
        res += f"  name={self.name},\n"
        res += f"  examType={self.examType},\n"
        res += f"  start={self.start},\n"
        res += f"  end={self.end},\n"
        res += f"  location={self.location}\n"
        res += ")"
        return res

    @property
    def summary(self) -> str:
        return f"[务必核对!]{self.name} {self.examType.value}"

    @property
    def locationString(self) -> str:
        res = ""
        if self.location is not None:
            res += self.location
        else:
            res += "地点待定"
        if self.seat is not None:
            res += f" (座位号: {self.seat})"
        return res

    @property
    def description(self) -> str:
        return "学分: %.1f" % self.credit


class ExamTable:
    exams: list[Exam]

    def __init__(self):
        self.exams: list[Exam] = []

    def __repr__(self) -> str:
        return str(self.exams)

    def fromZdbk(self, raw: list[dict]) -> None:
        ZDBK = Exam.SCHEME_ZDBK
        for item in raw:
            if "qzkssj" in item:
                self.exams.append(Exam(item, ZDBK, ExamType.MidTerm))
            if "kssj" in item:
                self.exams.append(Exam(item, ZDBK, ExamType.FinalTerm))
            if "qzkssj" not in item and "kssj" not in item:
                self.exams.append(Exam(item, ZDBK, ExamType.NoExam))

    def find(self, course: "Course") -> list[Exam]:
        res = []
        for exam in self.exams:
            if exam.classId == course.classId:
                assert exam.name == course.name
                res.append(exam)
        return res

    def toEvents(self, courses: "CourseTable") -> list[Event]:
        log.info("开始生成考试日历事件")

        try:
            events: list[Event] = []

            for course in courses.courses:
                for exam in self.find(course):
                    if exam.examType == ExamType.NoExam:
                        continue
                    if exam.isEventGenerated:
                        continue

                    exam.isEventGenerated = True
                    events.append(Event(
                        summary=exam.summary,
                        location=exam.locationString,
                        description=exam.description,
                        start=exam.start,
                        end=exam.end
                    ))
        except Exception as e:
            log.error(f"考试日历事件生成失败: {e}")
            raise e

        return events
