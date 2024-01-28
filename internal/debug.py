from datetime import datetime
from typing import List, Coroutine, Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from env import Env
from schemas.config import RunEnvironment


class DebugManager:
    """Manages debugging."""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.secs = 2

    def init(self):
        if Env.run_env == RunEnvironment.testing:
            self.scheduler.start()

    def change_tasks(self, tasks: List[Coroutine[Any, Any, None]]):
        """Changes current task."""
        self.scheduler.remove_all_jobs()
        for i in tasks:
            self.scheduler.add_job(func=i,
                                   trigger="interval",
                                   seconds=self.secs,
                                   next_run_time=datetime.now(),
                                   id=f"testing_refresh_{i}")

    def change_secs(self, secs: int):
        """Changes seconds per run."""
        self.secs = secs


debug_manager = DebugManager()
