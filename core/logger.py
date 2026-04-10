"""日志模块 - 统一配置日志格式和输出"""

import logging
import sys
from pathlib import Path

import config


def setup_logger(
    name: str = "agent",
    level: int = logging.INFO,
    log_file: str = None,
) -> logging.Logger:
    """
    创建并配置 Logger。

    Args:
        name: logger 名称
        level: 日志级别
        log_file: 日志文件名（相对于 WORKSPACE_DIR），为 None 则不写文件

    Returns:
        配置好的 Logger 实例
    """
    logger = logging.getLogger(name)

    # 避免重复添加 handler（模块被多次 import 时）
    if logger.handlers:
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台 handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # 文件 handler（可选）
    if log_file:
        log_path = config.WORKSPACE_DIR / log_file
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(str(log_path), encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    获取子 logger。

    用法: logger = get_logger(__name__)
    返回 "agent.core.file_utils" 之类的子 logger，
    只要根 "agent" logger 已配置，子 logger 自动继承。
    """
    return logging.getLogger(f"agent.{name}")
