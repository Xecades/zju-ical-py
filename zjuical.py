import argparse
import os

from loguru import logger

from main.integration import getCalender
from utils.config import config

VERSION = "1.1.0"

if __name__ == "__main__":

    def formatter(prog):
        return argparse.HelpFormatter(prog, max_help_position=52)

    parser = argparse.ArgumentParser(
        prog="zjuical.py",
        description="A command-line utility for generating \
            class schedule iCalender file from extracting \
            data from ZJU ZDBK API. Refactored based \
            on Python by Xecades.",
        formatter_class=formatter,
    )
    parse = parser.add_argument

    parse(
        "-u",
        "--username",
        type=str,
        required=True,
        help="ZJUAM username",
    )
    parse(
        "-p",
        "--password",
        type=str,
        required=True,
        help="ZJUAM password",
    )
    parse(
        "-c",
        "--config",
        type=str,
        default="configs/config.json",
        help='config file (default "configs/config.json")',
    )
    parse(
        "-a",
        "--all",
        action="store_true",
        help="generate calendar for all config.*.json files in configs folder (overrides --config)",
    )
    parse(
        "-o",
        "--output",
        type=str,
        default="zjuical.ics",
        help='output file (default "zjuical.ics")',
    )
    parse(
        "-f",
        "--force",
        action="store_true",
        help="force write to target file",
    )
    parse(
        "--skip-verification-and-use",
        type=str,
        choices=["grs", "ugrs"],
        help="skip verification for student id format, and use specified login method",
    )
    parse(
        "--delay",
        type=float,
        default=1.5,
        help="delay between requests in seconds (default 1.5)",
    )
    parse(
        "--include-todos",
        action="store_true",
        help="include todos (homework deadlines) in the calendar",
    )
    parse(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s v{VERSION}",
        help="version for zjuical",
    )

    args = parser.parse_args()

    logger.info(f"ZJU-ICAL-PY (v{VERSION}) by Xecades")

    if os.path.exists(args.output):
        if not args.force:
            logger.error(f"输出文件 {args.output} 已存在，请使用 -f 参数强制覆盖")
            exit(1)
        else:
            logger.warning(f"输出文件 {args.output} 已存在，将被覆盖")

    if args.all:
        logger.info("使用 --all 模式，将生成所有配置文件的日历")
        config.loadAll()
    else:
        config.load(args.config)

    cal = getCalender(
        args.username,
        args.password,
        args.skip_verification_and_use,
        args.delay,
        args.include_todos,
    )
    with open(args.output, "w", encoding="utf-8") as f:
        logger.info(f"正在写入文件 {args.output}")
        f.write(cal)

    logger.success("日历文件生成完毕")
