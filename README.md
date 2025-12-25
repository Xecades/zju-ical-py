# ZJU-ICAL-PY

> [!NOTE]
> 本项目是基于 [ZJU-ICAL 项目](https://github.com/cxz66666/zju-ical)的 Python 重构版本，更换了调用 API，目前**支持本科生和研究生的课程表**生成。本文档部分参考原项目的 README。
>
> 原项目按 LGPL-2.1 协议开源，本项目继承了原项目的协议。
>
> 研究生系统的 API 调用参考了 [Celechron 项目](https://github.com/Celechron/Celechron/blob/main/lib/http/zjuServices/grs_new.dart)。

将 ZJU 本科生/研究生课程表转换为 iCal 日历格式，方便地导入到 Windows/macOS/Linux/Android/Harmony OS/iOS/iPadOS/watchOS/Wear OS 上，支持：

-   自动调休安排（由作者不定期维护）
-   考试安排，包括考点教室、考试座位（**目前仅支持本科生**）

> [!WARNING]
> 当前项目仍处于测试阶段，可能存在未知的问题，欢迎提交 Issue 或 Pull Request。

## 免责声明

**该项目仅供学习交流使用，作者不对产生结果正确性与时效性做实时保证，使用者需自行承担因程序逻辑错误或课程时间变动导致的后果。**

所有服务均在使用者的本地设备上运行，ZJUAM 登录密码加密传输，不会存在任何有关用户隐私的蓄意记录/收集行为。

## 开始使用

首先使用 `git` 将本项目克隆到本地，安装 **3.12** 及以上的 Python 环境（更低版本未经测试），然后使用以下命令安装依赖库：

```sh
pip install -r requirements.txt
```

> [!CAUTION]
> 由于所有代码均在本地运行，请在使用前使用 `git pull` 确保代码是最新的，**尤其是调休安排发生了更新的时候**，你也可能希望在考试安排出来之后重新运行程序来获得考试地点、座位等信息。

`zjuical.py` 即为主程序，使用以下命令运行：

```sh
python zjuical.py -u [username] -p '[password]'
```

其中 `[username]` 为浙江大学统一身份认证用户名（即学号），`[password]` 为统一认证密码，无需方括号，外部引号需保留（防止密码中有特殊字符导致参数传递错误）。例如，假如你的学号为 3230100000，密码为 123456，那么你需要运行：

```sh
python zjuical.py -u 3230100000 -p '123456'
```

运行后即可在当前目录下生成 `zjuical.ics` 文件，导入到日历应用即可，更多的参数请使用 `python zjuical.py --help` 查看。

## 代码更新

由于代码完全在本地运行，所以**需要用户手动更新仓库**，强烈建议在每次运行前使用 `git pull` 命令更新代码，以确保获取到最新的调休安排和考试安排。

## 进阶使用 / `webical.py`

如果你想省去每次**代码更新**、**手动运行**的麻烦，可以使用 `webical.py` 脚本，它会在后台自动更新自身代码、运行并生成日历文件，并提供 HTTP 服务，从而能够在日历软件中直接订阅。

> [!CAUTION]
> 部分日历软件要求订阅链接**可在公网访问**，例如 Apple Calendar。因此以下步骤假定你已拥有一个公网 IP 或域名。除此之外，**理论上**日历的爬取是需要 ZJU 校网的，因此可能需要使用 [zju-connect](https://github.com/Mythologyli/zju-connect) 等工具在服务器上部署校网 VPN。（但是本人在测试的时候发现偶尔不需要校网也能访问，如果你能正常使用可以忽略这一步）
>
> **注意**：当前 `webical.py` 未做 HTTP Auth 鉴权，因此任何人只要知道你的公网 IP 和端口号就能访问你的日历文件，存在一定的隐私风险，请谨慎使用，见 [\#6](https://github.com/Xecades/zju-ical-py/issues/6)。

在安装完依赖后，使用以下命令运行：

```sh
python webical.py "[传递给zjuical.py的参数]"
# 例如:
# python webical.py "-u 3230100000 -p '123456' -f"
```

注意，**引号必须保留**，其内部的值会被直接传递给 `zjuical.py` 作为参数。默认设定每隔 1 小时自动更新并运行一次日历爬取，由于 `zjuical.py` 会生成 `zjuical.ics` 文件，因此你**必须在其中添加 `-f` 参数**以强制覆盖之前的文件，否则会导致日历文件无法更新。

除此之外，可通过 `-p` 参数指定 HTTP 服务端口，默认端口为 5273。开启服务后，你可以在日历软件中订阅 `http://[你的公网IP]:5273/zjuical.ics`。使用 `--help` 可查看更多参数。

## 开发计划

-   [x] 提供网页版订阅，自动推送更新
-   [x] 支持研究生课程表 by [\#11](https://github.com/Xecades/zju-ical-py/pull/11)
    -   [ ] 支持研究生考试安排
-   [ ] 提供更安全的传参方式
-   [ ] 整合 zju-connect

## 贡献代码

欢迎提交 Issue 或 Pull Request！请在贡献代码前，安装 `ruff` 并使用

```sh
ruff format .
ruff check --fix .
```

对代码进行格式化和检查，以保证代码风格一致。
