import requests
from course.course import CourseTable
from exam.exam import ExamTable
from utils.const import Term
from abc import ABC, abstractmethod


class Zjuam(ABC):
    LOGIN_URL = "https://zjuam.zju.edu.cn/cas/login"
    PUBKEY_URL = "https://zjuam.zju.edu.cn/cas/v2/getPubKey"

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.r = requests.Session()

    @abstractmethod
    def login(self) -> None:
        pass

    @abstractmethod
    def getCourses(self, year: str, term: Term, exams: ExamTable) -> CourseTable:
        pass
