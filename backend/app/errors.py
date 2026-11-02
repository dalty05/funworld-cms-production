# errors.py


from flask import jsonify
from flask_limiter.errors import RateLimitExceeded
from werkzeug.exceptions import HTTPException
from structlog import get_logger

from flask import g
from app.models import utcnow  # or datetime.utcnow(timezone.utc)





log = get_logger("app.errors")


class AppError(Exception):
    status, code, message = 400, "app_error", "An error occurred."

    def __init__(self, message=None, details=None, code=None, status=None):
        if message: self.message = message
        self.details = details or {}
        if code: self.code = code
        if status: self.status = status


class NotFoundError(AppError):     status, code = 404, "not_found"
class ValidationError(AppError):   status, code = 422, "validation_error"
class ConflictError(AppError):     status, code = 409, "conflict"
class ForbiddenError(AppError):    status, code = 403, "forbidden"
class UnauthorizedError(AppError): status, code = 401, "unauthorized"
class IdempotencyError(AppError):   status, code = 422, "idempotency_key_reuse"

class IdempotencyInFlightError(AppError):status, code = 409, "idempotency_in_flight"


# def ok(data=None, meta=None, status=200):
#     meta = meta or {}
#     meta.setdefault("request_id", getattr(g, "request_id", None))
#     meta.setdefault("timestamp", utcnow().isoformat())
    
#     return jsonify({"data": data or {}, "meta": meta}), status




def ok(data=None, meta=None, status=200):
    meta = dict(meta or {})
    meta.setdefault("request_id", getattr(g, "request_id", None))
    meta.setdefault("timestamp", utcnow().isoformat())

    return jsonify({
        "data": {} if data is None else data,
        "meta": meta,
    }), status




def error(code, message, details=None, status=400):
    return jsonify({
        "error": {"code": code, "message": message, "details": details or {}},
        "meta": {"request_id": getattr(g, "request_id", None),
                 "timestamp": utcnow().isoformat()},
    }), status


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def _app(e):
        log.warning("app_error", code=e.code, message=e.message)
        return error(e.code, e.message, e.details, e.status)

    @app.errorhandler(RateLimitExceeded)
    def _rate_limited(e):
        log.warning("rate_limit_exceeded", description=str(e))
        return error(
            "rate_limited",
            "Too many requests. Please slow down.",
            status=429,
        )

    @app.errorhandler(HTTPException)
    def _http(e):
        return error(e.name.lower().replace(" ", "_"), e.description, status=e.code)

    @app.errorhandler(Exception)
    def _unhandled(e):
        import traceback
        traceback.print_exc()          # <── add this
        log.exception("unhandled")
        return error("internal_error", "Unexpected error.", status=500)