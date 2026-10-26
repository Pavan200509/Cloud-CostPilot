"""Simple in-process refresh for connected project."""

from __future__ import annotations

import logging
import threading
from typing import Callable

log = logging.getLogger("costpilot.scheduler")


class RefreshScheduler:
    def __init__(self) -> None:
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()
        self._project_id: str | None = None
        self._interval = 300
        self._job: Callable[[str], None] | None = None

    def configure(self, interval_seconds: int, job: Callable[[str], None]) -> None:
        self._interval = interval_seconds
        self._job = job

    def set_project(self, project_id: str | None) -> None:
        with self._lock:
            self._project_id = project_id
            self._restart()

    def _restart(self) -> None:
        if self._timer:
            self._timer.cancel()
            self._timer = None
        if not self._project_id or not self._job:
            return
        self._timer = threading.Timer(self._interval, self._tick)
        self._timer.daemon = True
        self._timer.start()

    def _tick(self) -> None:
        project_id = self._project_id
        job = self._job
        if not project_id or not job:
            return
        try:
            job(project_id)
        except Exception:
            log.exception("Scheduled refresh failed for %s", project_id)
        finally:
            with self._lock:
                self._restart()


scheduler = RefreshScheduler()