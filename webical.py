import time
import sys
import argparse
import subprocess
import threading
from waitress import serve
from loguru import logger
from flask import Flask, Response

app = Flask(__name__)
VERSION = "1.0.0"
INTERVAL = 60 * 60  # 1 hour


def parse_args():
    def formatter(prog):
        return argparse.HelpFormatter(prog, max_help_position=52)

    parser = argparse.ArgumentParser(
        prog="webical.py",
        description="Web server for ZJU-ICAL-PY that performs \
            code & data updates automatically every hour, and \
            serves the latest iCalendar file.",
        formatter_class=formatter
    )
    parse = parser.add_argument

    parse("-p", "--port", type=int, default=5273,
          help="port to run the web server on")
    parse("--host", type=str, default="127.0.0.1",
          help="host of the web server (just for display)")
    parse("-v", "--version", action="version",
          version=f"%(prog)s v{VERSION}", help="version for zjuical web server")
    parse("zjuical", type=str,
          help="arguments for zjuical.py, e.g. '-u [username] -p [password]'")

    return parser.parse_args()


def git_pull():
    logger.info("执行 Git pull 命令以更新源代码...")
    result = subprocess.run(["git", "pull"], capture_output=True, text=True)
    logger.info(f"Git pull 输出: {result.stdout.strip()}")
    if result.returncode != 0:
        logger.error(f"Git pull 失败: {result.stderr.strip()}")
    else:
        logger.success("Git pull 成功")


def run_zjuical(zjuical_args: str):
    executable = sys.executable
    cmd = [executable, "zjuical.py"] + zjuical_args.split()
    logger.info("启动 zjuical.py...")
    print()
    subprocess.run(cmd)
    print()
    logger.info("zjuical.py 执行完毕")


def periodic_task(zjuical_args: str):
    try:
        git_pull()
        run_zjuical(zjuical_args)
    except Exception as e:
        logger.error(f"Periodic task 错误: {e}")
    logger.info(f"等待 {INTERVAL} 秒后再次执行任务...")
    time.sleep(INTERVAL)


@app.route("/zjuical.ics")
def serve_file():
    with open("zjuical.ics", "r") as f:
        content = f.read()
    return Response(content, mimetype="text/calendar")


if __name__ == "__main__":
    args = parse_args()
    logger.info(f"ZJU-ICAL-PY WEB-SERVER (v{VERSION}) by Xecades")
    logger.info(f"日历访问地址为 http://{args.host}:{args.port}/zjuical.ics")

    t = threading.Thread(
        target=periodic_task,
        daemon=True,
        args=(args.zjuical,)
    )
    t.start()

    serve(app, host="0.0.0.0", port=args.port)
