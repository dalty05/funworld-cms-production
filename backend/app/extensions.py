import os

from celery import Celery
from flask import g, request
from flask_jwt_extended import decode_token
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_talisman import Talisman

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
talisman = Talisman()


def _rate_limit_key() -> str:
    user = getattr(g, "current_user", None)
    if user is not None:
        return f"user:{user.id}"
    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() == "bearer" and token:
        try:
            claims = decode_token(token)
            if claims.get("sub"):
                return f"user:{claims['sub']}"
        except Exception:
            pass
    return f"ip:{get_remote_address()}"


limiter = Limiter(
    key_func=_rate_limit_key,
    default_limits=["300 per minute"],
    headers_enabled=True,
    strategy="moving-window",
    storage_uri="memory://",
)

# Module-level handles — None if not configured / not reachable
redis_client = None
celery = None


def init_redis(app):
    """
    Initialise Redis only if REDIS_URL is set AND reachable.

    If Redis is unavailable:
      - app still boots
      - redis_client stays None
      - idempotency falls back to Postgres-only (see security.py)
    """
    global redis_client

    url = (app.config.get("REDIS_URL") or "").strip()

    if not url:
        app.logger.warning("[redis] REDIS_URL not set — running without Redis")
        redis_client = None
        return

    if not url.startswith(("redis://", "rediss://", "unix://")):
        app.logger.warning(
            f"[redis] Invalid REDIS_URL scheme ({url!r}) — running without Redis"
        )
        redis_client = None
        return

    try:
        from redis import Redis
        client = Redis.from_url(url, decode_responses=True, socket_connect_timeout=2)
        client.ping()  # verify reachable
        redis_client = client
        app.logger.info(f"[redis] connected to {url}")
    except Exception as e:
        app.logger.warning(f"[redis] not reachable ({e}) — running without Redis")
        redis_client = None


def init_celery(app):
    """
    Celery is also optional. If Redis (or the broker URL) is unavailable,
    we skip worker registration entirely. Business logic that would publish
    tasks will fall back to synchronous execution or no-op.
    """
    global celery

    broker = (app.config.get("CELERY_BROKER_URL") or "").strip()
    backend = (app.config.get("CELERY_RESULT_BACKEND") or "").strip()

    if not broker.startswith(("redis://", "rediss://", "amqp://", "sqla+")):
        app.logger.warning("[celery] no valid broker — running without Celery")
        celery = None
        return

    try:
        c = Celery(
            app.import_name,
            broker=broker,
            backend=backend or None,
        )
        c.conf.update(app.config)

        class ContextTask(c.Task):
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)

        c.Task = ContextTask
        celery = c
        app.logger.info(f"[celery] configured with broker {broker}")
    except Exception as e:
        app.logger.warning(f"[celery] failed to configure ({e})")
        celery = None