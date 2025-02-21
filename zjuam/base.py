import requests
from course.course import Course
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
    def getCourses(self, year: str, term: str) -> list[Course]:
        pass
