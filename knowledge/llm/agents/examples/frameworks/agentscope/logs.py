from agentscope.message import Msg
import logging
import datetime
from pathlib import Path
import json


RUN_ID = datetime.datetime.now().strftime("%Y%m%d%H%M")
LOG_ROOT = Path("logs") / RUN_ID
LOG_ROOT.mkdir(parents=True, exist_ok=True)

INTERNAL_TYPES = {"thinking", "tool_use", "tool_result"}


def create_agent_logger(agent_name: str) -> logging.Logger:
    logger = logging.getLogger(f"agent.{agent_name}")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    if not logger.handlers:
        handler = logging.FileHandler(
            LOG_ROOT / f"{agent_name}.log",
            encoding="utf-8",
        )
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
