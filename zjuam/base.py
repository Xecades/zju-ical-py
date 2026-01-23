import json
import time
from abc import ABC, abstractmethod

import requests
from loguru import logger

from course.course import CourseTable
from exam.exam import ExamTable
from todos.todos import TodoTable
from utils.const import Term


class Zjuam(ABC):
    LOGIN_URL = "https://zjuam.zju.edu.cn/cas/login"
    PUBKEY_URL = "https://zjuam.zju.edu.cn/cas/v2/getPubKey"
    TODOS_URL = "https://courses.zju.edu.cn/api/todos"

    def __init__(self, username: str, password: str, request_delay: float = 1.5):
        self.username = username
        self.password = password
        self.request_delay = request_delay
        self.r = requests.Session()

    @abstractmethod
    def login(self) -> None:
        pass

    @abstractmethod
    def getCourses(self, year: str, term: Term, exams: ExamTable) -> CourseTable:
        pass

    @abstractmethod
    def getExams(self) -> ExamTable:
        pass

    def getTodos(self) -> TodoTable:
        # /api/todos is shared between ugrs and grs
        logger.info("开始获取待办事项信息")
        res = None
        try:
            time.sleep(self.request_delay)
            res = self.r.get(self.TODOS_URL)
            content = res.json()
            todo_list = content.get("todo_list", [])
            tt = TodoTable()
            tt.fromRes(todo_list)
        except json.JSONDecodeError as e:
            logger.error(f"待办事项信息获取失败: {e}")
            if res is not None:
                logger.info(f"返回内容: {res.text}")
            raise e
        except Exception as e:
            logger.error(f"待办事项信息获取失败: {e}")
            raise e
        logger.success(f"待办事项信息获取成功，共 {len(todo_list)} 项")
        return tt
