# Undergraduate Students
import re
from zjuam.base import Zjuam
from course.course import CourseTable
from exam.exam import ExamTable
from utils.const import Term
from loguru import logger
from course.convert import ugrsClassTermToQueryString


class UgrsZjuam(Zjuam):
    COURSE_URL = "http://zdbk.zju.edu.cn/jwglxt/kbcx/xskbcx_cxXsKb.html"
    EXAM_URL = "http://zdbk.zju.edu.cn/jwglxt/xskscx/kscx_cxXsgrksIndex.html?doType=query&queryModel.showCount=%s"
    ZDBK_LOGIN_URL = "https://zjuam.zju.edu.cn/cas/login?service=http%3A%2F%2Fzdbk.zju.edu.cn%2Fjwglxt%2Fxtgl%2Flogin_ssologin.html"

    def __init__(self, username: str, password: str):
        super().__init__(username, password)

    def login(self) -> None:
        logger.info("开始通过 ZJUAM 本科生途径登录")

        # stage 1: get csrf key
        try:
            res = self.r.get(self.ZDBK_LOGIN_URL)
            assert res.status_code == 200, "状态码错误"
            regex = r"\"execution\" value=\"(.*?)\" \/>"
            csrf = re.search(regex, res.text).group(1)
            assert csrf, "CSRF Key 为空"
        except Exception as e:
            logger.error(f"CSRF Key 获取失败: {e}")
            raise e
        logger.success("CSRF Key 获取成功")

        # stage 2: get pub key
        try:
            res = self.r.get(self.PUBKEY_URL)
            pubkey = res.json()
            N, E = pubkey["modulus"], pubkey["exponent"]
            N, E = int(N, 16), int(E, 16)
            plain = int.from_bytes(self.password.encode(), "big")
            cipher = hex(pow(plain, E, N))[2:]
            cipher = "0" * (128 - len(cipher)) + cipher
        except Exception as e:
            logger.error(f"RSA 公钥获取失败: {e}")
            raise e
        logger.success("RSA 公钥获取成功")

        # stage 3: fire target
        try:
            res = self.r.post(self.LOGIN_URL, data={
                "username": self.username,
                "password": cipher,
                "authcode":  "",
                "execution": csrf,
                "_eventId":  "submit",
            })
            assert "用户名或密码错误" not in res.text, "用户名或密码错误，请确保用户名密码正确后再运行程序，否则有账号被锁定的风险"
            assert "账号被锁定" not in res.text, "输错密码次数太多，账号被锁定，请过段时间再使用"
        except Exception as e:
            logger.error(f"ZJUAM 登录失败: {e}")
            raise e
        logger.success("ZJUAM 登录成功")

    def getCourses(self, year: str, term: Term, exams: ExamTable) -> CourseTable:
        logger.info(f"开始获取[{year}-{term.value}]课程信息")
        try:
            termQuery = ugrsClassTermToQueryString(term)
            assert termQuery, "学期参数错误"
            res = self.r.post(self.COURSE_URL, data={
                "xnm": year,
                "xqm": termQuery,
            }).json()

            res = res["kbList"]
            ct = CourseTable()
            ct.fromZdbk(res)
            ct.merge()
            ct.communicate(exams)
        except Exception as e:
            logger.error(f"课程信息获取失败: {e}")
            raise e
        logger.success(f"[{year}-{term.value}]课程信息获取成功")
        return ct

    def getExams(self, count: int = 5000) -> ExamTable:
        logger.info("开始获取考试信息")
        try:
            res = self.r.post(self.EXAM_URL % count).json()
            res = res["items"]
            et = ExamTable()
            et.fromZdbk(res)
        except Exception as e:
            logger.error(f"考试信息获取失败: {e}")
            raise e
        logger.success("考试信息获取成功")
        return et
