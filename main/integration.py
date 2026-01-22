from loguru import logger

from ical.ical import Calender
from utils.config import ClassYearAndTerm, TermConfig, config
from zjuam.base import Zjuam
from zjuam.grs import GrsZjuam
from zjuam.ugrs import UgrsZjuam


def getCalender(
    username: str,
    password: str,
    skip_verification_and_use: str | None,
    request_delay: float = 1.5,
) -> str:
    zjuam: Zjuam | None = None

    match username[0]:
        case "3":
            logger.info("检测到本科生学号，使用本科生途径登录")
            zjuam = UgrsZjuam(username, password, request_delay)
        case "1" | "2":
            logger.info("检测到研究生学号，使用研究生途径登录")
            zjuam = GrsZjuam(username, password, request_delay)
        case _:
            if skip_verification_and_use == "ugrs":
                logger.warning("跳过学号验证，使用本科生途径登录")
                zjuam = UgrsZjuam(username, password, request_delay)
            elif skip_verification_and_use == "grs":
                logger.warning("跳过学号验证，使用研究生途径登录")
                zjuam = GrsZjuam(username, password, request_delay)
            else:
                logger.error("学号不以 1/2/3 开头，不确保本项目能在除本科生/研究生之外的账号使用")
                logger.info(
                    "你可以通过 --skip-verification-and-use 参数跳过此检查，"
                    "同时欢迎向作者反馈其他类型账号使用情况"
                )
                raise NotImplementedError("不支持的用户类型")

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
        cal.addEvents(courseEvents)

        if exams is not None:
            examEvents = exams.toEvents(courses)
            cal.addEvents(examEvents)

    return cal.getICS(icalName=config.toTermString() + "课程表")
