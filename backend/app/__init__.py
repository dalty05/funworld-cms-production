# app/__init__.py
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO

from app.config import get_config
from app.extensions import db, migrate, init_redis, init_celery, limiter, talisman
from app.errors import register_error_handlers


jwt = JWTManager()
socketio = SocketIO(cors_allowed_origins="*")


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(config or get_config())

    if not app.config.get("DEBUG") and not app.config.get("TESTING"):
        secret_values = (app.config.get("SECRET_KEY"), app.config.get("JWT_SECRET_KEY"))
        if any(not value or value.endswith("dev-me") or len(value) < 32 for value in secret_values):
            raise RuntimeError("Production SECRET_KEY and JWT_SECRET_KEY must be unique strong values.")
        origins = app.config.get("CORS_ORIGINS", [])
        if isinstance(origins, str):
            origins = [origin.strip() for origin in origins.split(",") if origin.strip()]
        if not origins or any(
            "*" in origin or "localhost" in origin.lower()
            or "127.0.0.1" in origin or not origin.startswith("https://")
            for origin in origins
        ):
            raise RuntimeError("Production CORS_ORIGINS must list explicit HTTPS public origins only.")
        if app.config.get("RATELIMIT_ENABLED") and not str(
            app.config.get("RATELIMIT_STORAGE_URI", "")
        ).startswith(("redis://", "rediss://")):
            raise RuntimeError("Production rate limits require a Redis RATELIMIT_STORAGE_URI.")
        if not app.config.get("ENABLE_HSTS"):
            raise RuntimeError("Set ENABLE_HSTS=true in production after confirming HTTPS at the edge.")

    trusted_proxy_hops = app.config.get("TRUSTED_PROXY_HOPS", 0)
    if trusted_proxy_hops > 0:
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(
            app.wsgi_app,
            x_for=trusted_proxy_hops,
            x_proto=trusted_proxy_hops,
            x_host=trusted_proxy_hops,
        )

    origins = app.config.get("CORS_ORIGINS", [])
    if isinstance(origins, str):
        origins = [origin.strip() for origin in origins.split(",") if origin.strip()]
    app.config["CORS_ORIGINS"] = origins

    # Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    from app.security import is_token_revoked
    jwt.token_in_blocklist_loader(is_token_revoked)
    CORS(
        app,
        resources={r"/api/.*": {"origins": origins}},
        methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
        allow_headers=[
            "Content-Type", "Authorization", "Idempotency-Key",
            "X-Request-ID", "X-Initiator",
        ],
        expose_headers=["X-Request-ID", "X-Idempotent-Replay", "Retry-After"],
        supports_credentials=False,
        max_age=600,
    )
    limiter.init_app(app)
    talisman.init_app(
        app,
        force_https=False,
        strict_transport_security=bool(app.config.get("ENABLE_HSTS")),
        strict_transport_security_max_age=31536000,
        frame_options="DENY",
        content_security_policy={
            "default-src": ["'none'"],
            "frame-ancestors": ["'none'"],
            "base-uri": ["'none'"],
            "form-action": ["'none'"],
        },
        referrer_policy="strict-origin-when-cross-origin",
    )
    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Permitted-Cross-Domain-Policies", "none")
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        response.headers.setdefault(
            "Permissions-Policy", "geolocation=(), camera=(), microphone=()"
        )
        return response
    socketio.init_app(app, cors_allowed_origins=app.config.get("CORS_ORIGINS", ["*"]))
    init_redis(app)
    init_celery(app)

    from app.realtime import register_socket_events
    register_socket_events(socketio)

    # Blueprints
    from app.api import api_v1
    app.register_blueprint(api_v1, url_prefix="/api/v1")

    from app.cli import register_cli

    register_cli(app)

    if app.config.get("ENABLE_SCHEDULER") and not app.config.get("TESTING"):
        from app.scheduler import start_scheduler
        start_scheduler(app)

    # Error handling
    register_error_handlers(app)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app