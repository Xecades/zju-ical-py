import os
import json
from datetime import datetime, timedelta
from dataclasses import dataclass
from utils.const import Term, TweakMethod
from course.convert import isoToDate
from utils.logger import getLogger

log = getLogger(__name__)


@dataclass
class TermConfig:
    Year: str
    Term: Term
    Begin: datetime
    End: datetime
    FirstWeekNo: int


@dataclass
class Tweak:
    TweakType: TweakMethod
    Description: str
    From: datetime
    To: datetime


@dataclass
class ClassYearAndTerm:
    Year: str
    Term: Term


class Config:
    config: dict
    lastUpdated: datetime
    classTerms: list[ClassYearAndTerm]
    termConfigs: list[TermConfig]
    tweaks: list[Tweak]

    def __init__(self) -> None:
        pass

    def load(self, path: str) -> None:
        log.info("开始读取配置文件")

        if not os.path.exists(path):
            log.error(f"配置文件 {path} 不存在")
            exit(1)

        self.config = json.load(open(path, "r", encoding="utf-8"))
        self.lastUpdated = isoToDate(self.config["lastUpdated"])
        self.classTerms = []
        self.termConfigs = []
        self.tweaks = []

        for ct in self.config["classTerms"]:
            year, term = ct.split(":")
            term = Term(term)
            self.classTerms.append(ClassYearAndTerm(year, term))

        for tc in self.config["termConfigs"]:
            tc["Begin"] = isoToDate(tc["Begin"])
            tc["End"] = isoToDate(tc["End"])
            tc["Term"] = Term(tc["Term"])
            self.termConfigs.append(TermConfig(**tc))

        for tk in self.config["tweaks"]:
            tk["From"] = isoToDate(tk["From"])
            tk["To"] = isoToDate(tk["To"])
            tk["TweakType"] = TweakMethod(tk["TweakType"])
            self.tweaks.append(Tweak(**tk))

        log.info("配置文件读取处理完成")


config = Config()
