"""Run scheduled notification and expiry jobs as a standalone process."""

import signal
from threading import Event

from structlog import get_logger

from app import create_app
from app.scheduler import start_scheduler, stop_scheduler

log = get_logger("app.scheduler_runner")


def main():
    app = create_app()
    app.config["SCHEDULER_PROCESS"] = True
    scheduler = start_scheduler(app)
    if scheduler is None:
        raise RuntimeError("Scheduler failed to start.")

    stopped = Event()
    signal.signal(signal.SIGINT, lambda signum, frame: stopped.set())
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, lambda signum, frame: stopped.set())

    log.info("scheduler_runner_started")
    try:
        stopped.wait()
    finally:
        stop_scheduler()
        log.info("scheduler_runner_stopped")


if __name__ == "__main__":
    main()
