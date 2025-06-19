from ical.ical import Calender
from loguru import logger
from utils.config import config, ClassYearAndTerm, TermConfig
from zjuam.ugrs import UgrsZjuam


def getCalender(username: str, password: str, skip_verification: bool) -> str:
    if not username.startswith("3"):
        if skip_verification:
            logger.warning("跳过学号验证")
        else:
            logger.error("学号不以 3 开头，不确保本项目能在非本科生账号使用")
            logger.info(
                "你可以通过 --skip-verification 参数跳过此检查，同时欢迎向作者反馈非本科生账号使用情况")
            raise NotImplementedError("不支持的用户类型")

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
            logger.error(f"配置文件错误，未找到 {item.Year}-{item.Term.value} 的学期配置")
            exit(1)

        courses = zjuam.getCourses(item.Year, item.Term, exams)
        courseEvents = courses.toEvents(termConfig=tc)
        examEvents = exams.toEvents(courses)

        cal.addEvents(courseEvents)
        cal.addEvents(examEvents)

    return cal.getICS()
