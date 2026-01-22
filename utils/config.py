import glob
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
    is_all: bool = False

    def __init__(self) -> None:
        pass

    def toTermString(self) -> str:
        if self.is_all:
            return ""
        return self._toTermString(self.classTerms)

    @staticmethod
    def _toTermString(classTerms: list[ClassYearAndTerm]) -> str:
        terms: defaultdict[str, str] = defaultdict(str)
        for ct in classTerms:
            terms[ct.Year] += f"{ct.Term.value}"
        return ", ".join(f"{year} {terms[year]}" for year in sorted(terms.keys()))

    def load(self, path: str) -> None:
        logger.info("开始读取配置文件")
        self.is_all = False

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

    def loadAll(self) -> None:
        logger.info("开始读取所有配置文件")
        self.is_all = True

        config_files = sorted(glob.glob("configs/config*.json"))
        if not config_files:
            logger.error("未找到任何 config*.json 文件")
            exit(1)

        logger.info(
            f"找到 {len(config_files)} 个配置文件: {', '.join(os.path.basename(f) for f in config_files)}"
        )

        self.classTerms = []
        self.termConfigs = []
        self.tweaks = []
        latest_update = None

        for config_file in config_files:
            assert os.path.exists(config_file), f"配置文件 {config_file} 不存在，怎么可能？？"

            cfg = json.load(open(config_file, encoding="utf-8"))

            file_updated = isoToDate(cfg["lastUpdated"])
            if latest_update is None or file_updated > latest_update:
                latest_update = file_updated

            thisClassTerms: list[ClassYearAndTerm] = []

            # Merge classTerms
            for ct in cfg["classTerms"]:
                year, term = ct.split(":")
                term_obj = Term(term)
                class_term = ClassYearAndTerm(year, term_obj)
                if class_term not in self.classTerms:
                    thisClassTerms.append(class_term)

            self.classTerms.extend(thisClassTerms)
            logger.info(
                f"合并来自 {os.path.basename(config_file)} 的 {self._toTermString(thisClassTerms)}学期"
            )

            # Merge termConfigs
            for tc in cfg["termConfigs"]:
                tc["Begin"] = isoToDate(tc["Begin"])
                tc["End"] = isoToDate(tc["End"])
                tc["Term"] = Term(tc["Term"])
                term_config = TermConfig(**tc)

                # Check existing termConfigs
                if not any(
                    existing.Year == term_config.Year and existing.Term == term_config.Term
                    for existing in self.termConfigs
                ):
                    self.termConfigs.append(term_config)

            # Merge tweaks
            for tk in cfg["tweaks"]:
                tk["From"] = isoToDate(tk["From"])
                tk["To"] = isoToDate(tk["To"])
                tk["TweakType"] = TweakMethod(tk["TweakType"])
                tweak = Tweak(**tk)

                # Check existing tweaks
                if not any(
                    existing.From == tweak.From
                    and existing.To == tweak.To
                    and existing.TweakType == tweak.TweakType
                    for existing in self.tweaks
                ):
                    self.tweaks.append(tweak)

        self.lastUpdated = latest_update if latest_update else datetime.now()
        logger.info(f"所有配置文件读取处理完成，共合并 {len(self.classTerms)} 个学期")


config = Config()
