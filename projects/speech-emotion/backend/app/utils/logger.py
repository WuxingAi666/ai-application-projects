"""
日志配置模块
-----------
Windows 中文终端兼容 GBK，自动处理 emoji 字符
"""

import logging
import sys
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


class SafeStreamHandler(logging.StreamHandler):
    """安全的控制台处理器：自动处理 GBK 无法编码的字符"""

    def __init__(self, stream=None):
        super().__init__(stream)

    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            # 尝试写入，遇到编码错误时替换为 ?
            stream.write(msg + self.terminator)
            stream.flush()
        except UnicodeEncodeError:
            # GBK 不支持的字符，用 ASCII 替代方案
            stream = self.stream
            safe_msg = self.format(record).encode(
                sys.stdout.encoding or "gbk", errors="replace"
            ).decode(sys.stdout.encoding or "gbk", errors="replace")
            stream.write(safe_msg + self.terminator)
            stream.flush()
        except Exception:
            self.handleError(record)


def setup_logger(name: str = "ser") -> logging.Logger:
    """创建配置好的日志器"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台处理器（安全编码）
    console_handler = SafeStreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件处理器（UTF-8，保留完整信息）
    file_handler = logging.FileHandler(
        LOG_DIR / "ser.log", encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


logger = setup_logger("ser")
