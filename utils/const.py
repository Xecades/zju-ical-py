from enum import Enum, unique


@unique
class WeekType(Enum):
    Normal = 2      # 每周都有
    OddOnly = 0     # 单周
    EvenOnly = 1    # 双周


@unique
class Term(Enum):
    Autumn = "秋"          # 秋学期
    Winter = "冬"          # 冬学期
    ShortA = "短1"         # 短学期A (NotImplemented)
    SummerVacation = "暑"  # 暑学期  (NotImplemented)
    Spring = "春"          # 春学期
    Summer = "夏"          # 夏学期
    ShortB = "短2"         # 短学期B (NotImplemented)


@unique
class TweakMethod(Enum):
    Clear = "Clear"        # 清空 [From, To] 的所有课程
    Copy = "Copy"          # 从 From 复制到 To
    Move = "Move"          # 从 From 移动到 To
    Exchange = "Exchange"  # 交换 From 和 To 的课程


@unique
class ExamType(Enum):
    MidTerm = "期中考试"
    FinalTerm = "期末考试"
    NoExam = "无考试"
