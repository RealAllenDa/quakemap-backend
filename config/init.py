import os
import sys
import time

from loguru import logger

from env import Env
from schemas.config import ConfigModel, RunEnvironment
from sdk import yaml_to_model, relpath

__all__ = ["init_config"]


def init_config(run_type: RunEnvironment) -> None:
    """
    Initializes the config.

    :param run_type: The run type (production, development, etc.)
    """
    logger.remove()
    Env.config = yaml_to_model(relpath(f"{run_type.value}.yaml"), ConfigModel)
    Env.init_time = int(time.time())

    # --- Logger initialization
    if not os.path.exists(os.path.expanduser("./logs")):
        os.mkdir("logs")
    logger.add(
        sys.stdout,
        enqueue=True,
        backtrace=Env.config.logger.backtrace,
        diagnose=Env.config.logger.diagnose,
        level=Env.config.logger.level.value
    )
    logger.add(
        os.path.join("logs", "main.log"),
        retention=Env.config.logger.retention,
        rotation=Env.config.logger.rotation,
        enqueue=True,
        encoding="utf-8",
        backtrace=Env.config.logger.backtrace,
        diagnose=Env.config.logger.diagnose,
        level=Env.config.logger.level.value
    )
    sys.stdout.reconfigure(encoding="utf-8")
    logger.success("Logger initialized.")
