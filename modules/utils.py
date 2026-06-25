"""工具函数模块"""

import subprocess
from datetime import datetime

from .config import LOG_FILE


def now():
    """获取当前时间字符串"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log(line):
    """打印并写入日志"""
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def macos_notify(title, message):
    """macOS 通知"""
    subprocess.run([
        "osascript",
        "-e",
        f'display notification "{message}" with title "{title}" sound name "Sosumi"'
    ])


def macos_alert(title, message):
    """macOS 弹窗"""
    subprocess.run([
        "osascript",
        "-e",
        f'display dialog "{message}" with title "{title}" buttons {{"OK"}} default button "OK"'
    ])
