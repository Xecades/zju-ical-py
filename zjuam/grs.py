# Graduate Students
import re
import time
from urllib.parse import parse_qs, urlparse

from loguru import logger

from course.convert import grsClassTermToQueryString, grsGetYear
from course.grs_course import GRSCourseTable
from exam.exam import ExamTable
from utils.const import Term
from zjuam.base import Zjuam


class GrsZjuam(Zjuam):
    COURSE_URL = "https://yjsy.zju.edu.cn/dataapi/py/pyKcbj/queryXskbByLoginUser?"
    EXAM_URL = "https://yjsy.zju.edu.cn/dashboard/workplace?dm=py_grks"
    INFO_URL = "https://yjsy.zju.edu.cn/dataapi/py/pyXsxk/queryXsxkByXnxqXs"
    YJSY_LOGIN_URL = "https://zjuam.zju.edu.cn/cas/login?service=https%3A%2F%2Fyjsy.zju.edu.cn%2F"
    YJSY_TOKEN_URL = "https://yjsy.zju.edu.cn/dataapi/sys/cas/client/validateLogin?service=https:%2F%2Fyjsy.zju.edu.cn%2F"

    def __init__(self, username: str, password: str):
        super().__init__(username, password)

    def login(self) -> None:
        logger.info("开始通过 ZJUAM 研究生途径登录")

        # stage 1: get csrf key
        try:
            res = self.r.get(self.YJSY_LOGIN_URL)
            assert res.status_code == 200, "状态码错误"
            regex = r"\"execution\" value=\"(.*?)\" \/>"
            match = re.search(regex, res.text)
            assert match is not None, f"CSRF Key 正则匹配失败，返回内容: {res.text}"
            csrf = match.group(1)
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
            res = self.r.post(
                self.LOGIN_URL,
                data={
                    "username": self.username,
                    "password": cipher,
                    "authcode": "",
                    "execution": csrf,
                    "_eventId": "submit",
                },
            )
            assert "用户名或密码错误" not in res.text, (
                "用户名或密码错误，请确保用户名密码正确后再运行程序，否则有账号被锁定的风险"
            )
            assert "账号被锁定" not in res.text, "输错密码次数太多，账号被锁定，请过段时间再使用"
            self.sso_cookie = {"iPlanetDirectoryPro": self.r.cookies["iPlanetDirectoryPro"]}
        except Exception as e:
            logger.error(f"ZJUAM 登录失败: {e}")
            raise e
        logger.success("ZJUAM 登录成功")

        # stage 4: login yjsy
        try:
            # 第一步：使用SSO Cookie获取ticket
            response = self.r.get(
                self.YJSY_LOGIN_URL,
                cookies=self.sso_cookie,
                allow_redirects=False,  # 不自动跟随重定向
            )

            # 检查重定向位置
            location_header = response.headers.get("location")
            if not location_header:
                raise Exception("Invalid location header")

            # 从重定向URL中提取ticket参数
            parsed_url = urlparse(location_header)
            query_params = parse_qs(parsed_url.query)
            ticket = query_params.get("ticket", [None])[0]
            if not ticket:
                raise Exception("Invalid location header - no ticket found")

            # 第二步：使用ticket获取token
            second_url = self.YJSY_TOKEN_URL + f"&ticket={ticket}"
            response = self.r.get(second_url)

            # 解析JSON响应
            login_info = response.json()
            if not login_info.get("success"):
                raise Exception("Invalid login info")

            login_result = login_info.get("result", {})
            self._token = login_result.get("token")

            if not self._token:
                raise Exception("Invalid token")
        except Exception as e:
            logger.error(f"YJSY 登录失败: {e}")
            raise e
        logger.success("YJSY 登录成功")

    def getCourses(self, year: str, term: Term, exams: ExamTable) -> GRSCourseTable:
        logger.info(f"开始获取[{year}-{term.value}]课程信息")
        try:
            year = grsGetYear(year, term)
            termQuery = grsClassTermToQueryString(term)
            time.sleep(1.5)

            courseUrl = self.COURSE_URL + f"xn={year}&pkxq={termQuery}"
            res = self.r.get(courseUrl, headers={"X-Access-Token": self._token}).json()
            assert res.get("success"), "课程信息获取失败"
            res = res["result"]["kcbMap"]
            ct = GRSCourseTable()
            ct.fromRes(res)
            ct.deDup()

            res = self.r.post(self.INFO_URL, headers={"X-Access-Token": self._token}).json()
            assert res.get("success"), "课程附加信息获取失败"
            res = res["result"]["xxjhnList"]
            ct.grsGetInfo(res)

        except Exception as e:
            logger.error(f"课程信息获取失败: {e}")
            raise e
        logger.success(f"[{year}-{term.value}]课程信息获取成功")
        return ct

    # TODO: implement exam fetching for graduate system
    def getExams(self, count: int = 5000) -> ExamTable:
        logger.warning("研究生系统暂未适配考试信息查询")
        return ExamTable()  # empty exam table
