import json
import os
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

from loguru import logger

from course.convert import isoToDate
from utils.const import Term, TweakMethod


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

    def toTermString(self) -> str:
        terms: defaultdict[str, str] = defaultdict(str)
        for ct in self.classTerms:
            terms[ct.Year] += f"{ct.Term.value}"
        return ", ".join(f"{year} {terms[year]}" for year in sorted(terms.keys()))

    def load(self, path: str) -> None:
        logger.info("开始读取配置文件")

        if not os.path.exists(path):
            logger.error(f"配置文件 {path} 不存在")
            exit(1)

        self.config = json.load(open(path, encoding="utf-8"))
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

        logger.info("配置文件读取处理完成")


config = Config()
