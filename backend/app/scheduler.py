from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler
from structlog import get_logger

log = get_logger("app.scheduler")
_scheduler: BackgroundScheduler | None = None


def _run_task(app, name: str, task):
    with app.app_context():
        try:
            result = task()
        except Exception:
            log.exception("scheduled_task_failed", task=name)
            return

        if result:
            log.info("scheduled_task_completed", task=name, result=result)



def _publish_scheduled_posts():
    from app.services import publish_due_scheduled_posts
    return publish_due_scheduled_posts()




def start_scheduler(app) -> BackgroundScheduler | None:
    global _scheduler

    if app.config.get("TESTING"):
        return None
    if not (app.config.get("ENABLE_SCHEDULER") or app.config.get("SCHEDULER_PROCESS")):
        return None
    if _scheduler and _scheduler.running:
        return _scheduler

    scheduler = BackgroundScheduler(timezone="UTC", daemon=True)
  
    scheduler.add_job(
        _run_task, "interval", minutes=5,
        args=[app, "publish_scheduled_posts", _publish_scheduled_posts],
        id="publish_scheduled_posts", max_instances=1, coalesce=True,
    )
    scheduler.start()
    _scheduler = scheduler
    log.info("scheduler_started", jobs=1)
    return scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
    _scheduler = None
