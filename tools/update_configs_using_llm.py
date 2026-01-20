"""使用 DeepSeek API 生成 tweaks 配置"""

import json
import os
import sys
from pathlib import Path
from typing import cast

from dotenv import load_dotenv
from openai import OpenAI

SYSTEM_PROMPT = """你是一个专业的配置文件生成助手。你的任务是根据学校官网的节假日调休通知，生成结构化的 tweaks 配置。

## Tweak 类型说明

- **Clear**: 清空某个日期范围内的所有课程（用于连续多天的假期）
- **Move**: 将某一天的课程移动到另一天（停课并在另一天补课）
- **Exchange**: 交换两天的课程安排（对调）
- **Copy**: 从某天复制课程到另一天
- **Pending**: 表示待定，不起作用

## 输出格式

返回一个 JSON 数组，每个元素包含：

- TweakType: 类型（Clear/Move/Exchange/Copy/Pending）
- Description: 描述信息，格式为 "[节日名称] 具体说明"
- From: 起始日期，格式为 YYYYMMDD 的整数
- To: 目标日期，格式为 YYYYMMDD 的整数

## 示例输入

```
根据《浙江大学校长办公室关于2025年部分节假日安排的通知》，结合《浙江大学2025-2026学年校历》，现将2025年下半年部分节假日及学校活动期间的教学安排温馨提醒如下：

一、国庆节、中秋节

10月1日至8日放假调休，具体教学安排为：
10月1日（周三）至3日（周五）、6日（周一）停课，不统一安排补课；
10月7日（周二）、10月8日（周三）分别与9月28日（周日）、10月11日（周六）的课对调。

二、秋季校运动会

学校于10月24日至26日举行秋季校运动会。
10月24日（周五）停课，安排在10月18日（周六）补课。

三、浙江大学学生节

学校于12月31日举办浙江大学学生节。
12月31日（周三）停课，安排在2026年1月5日（周一）补课。
```

## 示例输出

```json
[
    {
        "TweakType": "Clear",
        "Description": "[国庆中秋] 10月1日（周三）至3日（周五）停课",
        "From": 20251001,
        "To": 20251003
    },
    {
        "TweakType": "Clear",
        "Description": "[国庆中秋] 10月6日（周一）停课",
        "From": 20251006,
        "To": 20251006
    },
    {
        "TweakType": "Exchange",
        "Description": "[国庆中秋] 10月7日（周二）与9月28日（周日）的课对调",
        "From": 20251007,
        "To": 20250928
    },
    {
        "TweakType": "Exchange",
        "Description": "[国庆中秋] 10月8日（周三）与10月11日（周六）的课对调",
        "From": 20251008,
        "To": 20251011
    },
    {
        "TweakType": "Move",
        "Description": "[秋季校运会] 10月24日（周五）停课，安排在10月18日（周六）补课",
        "From": 20251024,
        "To": 20251018
    },
    {
        "TweakType": "Move",
        "Description": "[学生节] 12月31日（周三）停课，安排在1月5日（周一）补课",
        "From": 20251231,
        "To": 20260105
    }
]
```

## 重要规则

1. **Clear** 类型：
    - 用于节假日期间的停课（无需补课的情况）
    - From 和 To 表示停课的日期范围（包含首尾）
    - 如果只停一天课，From 和 To 相同

2. **Move** 类型：
    - 用于"某天停课，安排在另一天补课"的情况
    - From 是停课日期，To 是补课日期
    - Description 格式：[节日/事件] X月X日（周X）停课，安排在X月X日（周X）补课

3. **Exchange** 类型：
    - 用于"两天的课对调"的情况
    - From 和 To 是互换的两天
    - Description 格式：[节日/事件] X月X日（周X）与X月X日（周X）的课对调

4. **Pending** 类型：
    - 用于无法确定具体安排的情况（一般是调休安排另行通知）
    - 如果明确给出日期，则 From 和 To 填写该日期，否则填 null
    - Description 格式：[节日/事件] 具体说明

5. **Copy** 类型：
    - 一般情况较少使用

6. 日期格式必须是 YYYYMMDD 的整数（如 20260101）

7. Description 必须以 "[节日/事件名称]" 开头，然后是简洁的具体说明

8. 直接输出 JSON 数组，不要包含其他内容或 markdown 代码块标记

9. Description 要简洁明了，直接使用通知中的关键信息

10. 尽量保证所有日期不重叠，例如有“5月1日至5日停课”和“6月22日补5月4日的课”，对于5月4日的停课，应优先使用 Move，不再需要 Clear

请仔细分析输入的通知内容，准确判断每个日期的调整类型，确保 Description 格式统一、简洁。"""


def read_input() -> str:
    if not sys.stdin.isatty():
        return sys.stdin.read()

    print("请粘贴学校官网的节假日调休通知（输入完成后按 Ctrl+D 或 Ctrl+Z）:")
    print("-" * 60)
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
    print("-" * 60)
    return "\n".join(lines)


def clean(content: str) -> str:
    cleaned = content.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()


def call_deepseek(api_key: str, user_input: str) -> dict:
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    stream = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ],
        stream=True,
    )

    content = ""
    for chunk in stream:
        d_content = chunk.choices[0].delta.content
        if d_content:
            content += d_content
            print(d_content, end="", flush=True)

    cleaned_content = clean(content)
    return cast(dict, json.loads(cleaned_content))


def save_output(tweaks: dict, output_path: Path):
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(tweaks, f, ensure_ascii=False, indent=4)

    print(f"\n配置已保存到: {output_path}")
    print("请仔细检查生成的配置是否正确，确认后再合并到 config.json")


def main():
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)

    api_key = os.getenv("API_KEY")
    if not api_key:
        print("错误: 未找到 API_KEY 环境变量")
        print(f"请在 {env_path} 文件中配置 API_KEY")
        sys.exit(1)

    user_input = read_input()
    if not user_input.strip():
        print("错误: 输入为空")
        sys.exit(1)

    try:
        tweaks = call_deepseek(api_key, user_input)
    except Exception as e:
        print(f"\n错误: API 调用失败 - {e}")
        sys.exit(1)

    output_path = Path(__file__).parent.parent / "configs" / "tweaks.to_be_validated.json"
    save_output(tweaks, output_path)


if __name__ == "__main__":
    main()
