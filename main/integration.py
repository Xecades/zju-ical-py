from ical.ical import Calender
from utils.logger import getLogger
from utils.config import config, ClassYearAndTerm, TermConfig
from course.course import Course
from zjuam.ugrs import UgrsZjuam

log = getLogger(__name__)


def getCalender(username: str, password: str) -> str:
    if not username.startswith("3"):
        log.error("当前只支持本科生日历生成，欢迎有能力的同学提交 PR 到本项目仓库")
        exit(1)

    zjuam = UgrsZjuam(username, password)
    zjuam.login()

    termConfigs = config.termConfigs

    def firstMatchTerm(item: ClassYearAndTerm) -> None | TermConfig:
        for tc in termConfigs:
            if tc.Year == item.Year and tc.Term == item.Term:
                return tc
        return None

    cal = Calender()
    exams = zjuam.getExams()

    for item in config.classTerms:
        tc = firstMatchTerm(item)
        if tc is None:
            log.error(f"配置文件错误，未找到 {item.Year}-{item.Term.value} 的学期配置")
            exit(1)

        courses = zjuam.getCourses(item.Year, item.Term)
        courseEvents = courses.toEvents(termConfig=tc)
        examEvents = exams.toEvents(courses)

        cal.addEvents(courseEvents)
        cal.addEvents(examEvents)

    return cal.getICS()
