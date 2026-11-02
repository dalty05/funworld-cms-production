# security.py
import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from functools import wraps
from app.models import utcnow  # or datetime.utcnow(timezone.utc)

import bcrypt
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    verify_jwt_in_request,
)
from sqlalchemy.exc import IntegrityError

from app.extensions import db, redis_client


from flask import current_app, g, jsonify, request
from app import db
from app.models import IdempotencyKey
from app.errors import UnauthorizedError, ForbiddenError

from app.errors import IdempotencyError, IdempotencyInFlightError, ValidationError,ConflictError




IDEMPOTENT_METHODS = {"POST", "PATCH", "PUT", "DELETE"}
IDEMPOTENCY_TTL = timedelta(hours=24)



def _request_body_hash() -> str:
    raw = request.get_data(as_text=True) or ""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _scope_for(user_id, endpoint: str) -> str:
    return f"user:{user_id}:endpoint:{endpoint}"


def check_idempotency():
    """
    Call at the top of any state-changing view.
    Returns cached response if replay; raises 422 if key reused with different body.
    """
    key = request.headers.get("Idempotency-Key")
    if not key or request.method not in IDEMPOTENT_METHODS:
        return None

    user_id = getattr(g, "user_id", None) or "anonymous"
    scope = _scope_for(user_id, request.endpoint)
    body_hash = _request_body_hash()

    existing = IdempotencyKey.query.filter_by(scope=scope, key=key).first()
    if existing and existing.expires_at < utcnow():
        db.session.delete(existing)
        db.session.commit()
        existing = None

    if existing:
        if existing.request_hash != body_hash:
            from app.errors import ApiError
            raise ApiError(
                "idempotency_key_reuse",
                "This idempotency key was used with a different request body.",
                422,
                details={"original_request_hash": existing.request_hash,
                         "received_request_hash": body_hash},
            )
        if existing.status == "processing":
            from app.errors import ApiError
            raise ApiError("idempotency_in_flight",
                           "A request with this key is still processing.", 409)
        return existing.response_status, existing.response_body

    record = IdempotencyKey(
        key=key, scope=scope, request_hash=body_hash,
        status="processing",
        expires_at=utcnow() + IDEMPOTENCY_TTL,
    )
    db.session.add(record)
    db.session.commit()
    g.idempotency_record_id = record.id
    return None


def record_idempotent_response(status: int, body: dict):
    rid = getattr(g, "idempotency_record_id", None)
    if not rid:
        return
    record = db.session.get(IdempotencyKey, rid)
    if record:
        record.status = "completed"
        record.response_status = status
        record.response_body = body
        db.session.commit()

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------
class PasswordPolicyError(ValueError):
    pass


_COMMON_PASSWORDS = {
    "password", "password123", "password1", "12345678", "123456789",
    "qwerty123", "admin123", "letmein", "welcome1", "funworld123",
}


def validate_password_strength(password: str) -> None:
    if not isinstance(password, str) or len(password) < 10:
        raise PasswordPolicyError("Password must be at least 10 characters.")
    if len(password.encode("utf-8")) > 72:
        raise PasswordPolicyError("Password must be 72 UTF-8 bytes or fewer.")
    if "\x00" in password:
        raise PasswordPolicyError("Password contains an unsupported character.")
    if password.casefold() in _COMMON_PASSWORDS:
        raise PasswordPolicyError("Password is too common. Choose another.")
    if not re.search(r"[A-Z]", password):
        raise PasswordPolicyError("Password must include an uppercase letter.")
    if not re.search(r"[a-z]", password):
        raise PasswordPolicyError("Password must include a lowercase letter.")
    if not re.search(r"\d", password):
        raise PasswordPolicyError("Password must include a digit.")
    if not re.search(r"[^A-Za-z0-9]", password):
        raise PasswordPolicyError("Password must include a symbol.")


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    validate_password_strength(password)
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    if not password or not password_hash:
        return False
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
    except (ValueError, TypeError):
        return False


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------
def issue_tokens(user_id: str, additional_claims: dict | None = None) -> dict:
    """Issue an access + refresh token pair with the user's revocation version."""
    from app.models import User

    user = db.session.get(User, user_id)
    claims = {"tv": int(user.token_version or 0) if user else 0}
    if additional_claims:
        claims.update(additional_claims)
    claims["tv"] = int(user.token_version or 0) if user else 0

    access = create_access_token(identity=str(user_id), additional_claims=claims)
    refresh = create_refresh_token(identity=str(user_id), additional_claims=claims)

    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "Bearer",
    }


def is_token_revoked(jwt_header: dict, jwt_payload: dict) -> bool:
    from app.models import RevokedToken

    jti = jwt_payload.get("jti")
    return not jti or db.session.get(RevokedToken, jti) is not None


def revoke_token(jwt_payload: dict) -> None:
    from app.models import RevokedToken

    jti = jwt_payload.get("jti")
    expires_at = jwt_payload.get("exp")
    if not jti or not expires_at:
        raise ValueError("JWT is missing its revocation identifiers.")
    if db.session.get(RevokedToken, jti) is None:
        db.session.add(RevokedToken(
            jti=jti,
            expires_at=datetime.fromtimestamp(float(expires_at), timezone.utc),
        ))


# ---------------------------------------------------------------------------
# Current user helpers
# ---------------------------------------------------------------------------
def _load_current_user():
    """Load the authenticated user from the JWT identity into g.current_user."""
    from app.models import User  # local import avoids circular import at boot

    identity = get_jwt_identity()
    if not identity:
        return None

    user = User.query.get(identity)
    if not user or not user.is_active:
        return None
    try:
        token_version = int(get_jwt().get("tv", 0))
    except (TypeError, ValueError):
        return None
    if token_version != int(user.token_version or 0):
        return None
    g.current_user = user
    return user


def current_user():
    return getattr(g, "current_user", None)


# ---------------------------------------------------------------------------
# Decorators
# ---------------------------------------------------------------------------




def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        if not _load_current_user():
            raise UnauthorizedError("Authentication required.")
        return fn(*args, **kwargs)
    return wrapper




def require_permission(code, scope_type=None, scope_from=None):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user = _load_current_user()
            if not user:
                raise UnauthorizedError("Authentication required.")

            scope_id = kwargs.get(scope_from) if scope_from else None
            if not user.has_permission(code, scope_type=scope_type, scope_id=scope_id):
                raise ForbiddenError(
                    f"Missing permission: {code}",
                    details={"permission": code},
                )
            return fn(*args, **kwargs)
        return wrapper
    return decorator











def can_grant_permission(granting_user, target_role, permission_code: str) -> bool:
    """
    A user cannot grant a permission they don't already hold.
    Owners bypass this (they hold everything).
    """
    if not granting_user.is_active:
        return False
    if granting_user.has_permission("role.assign"):
        # even role.assign doesn't let you escalate: you must already have the perm
        return granting_user.has_permission(permission_code)
    return False


def can_assign_role(granting_user, target_role) -> bool:
    """User can only assign roles whose permissions they themselves hold."""
    if not granting_user.has_permission("role.assign"):
        return False
    return all(
        granting_user.has_permission(p.code) for p in target_role.permissions
    )




# ---------------------------------------------------------------------------
# Idempotency middleware
# ---------------------------------------------------------------------------
def _hash_body(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _redis_key(scope: str, key: str) -> str:
    return f"idempotency:{scope}:{key}"


def _build_scope() -> str:
    user = current_user()
    user_part = str(user.id) if user else "anon"
    return f"user:{user_part}:endpoint:{request.method}:{request.path}"



def idempotent(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        key = request.headers.get("Idempotency-Key")
        if not key:
            return fn(*args, **kwargs)

        if len(key) > 64:
            raise ValidationError("Idempotency-Key too long (max 64 chars).")

        scope = _build_scope()
        body_hash = _hash_body(request.get_data() or b"")

        if redis_client is not None:
            try:
                cached = redis_client.get(_redis_key(scope, key))
                if cached:
                    payload = json.loads(cached)
                    response = jsonify(payload["body"])
                    response.status_code = payload["status"]
                    response.headers["X-Idempotent-Replay"] = "true"
                    return response
            except Exception:
                pass

        record = IdempotencyKey(
            key=key, scope=scope, request_hash=body_hash,
            status="processing",
            expires_at=datetime.now(timezone.utc)
            + timedelta(seconds=current_app.config.get("IDEMPOTENCY_TTL_SECONDS", 86400)),
        )
        db.session.add(record)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            existing = IdempotencyKey.query.filter_by(scope=scope, key=key).first()
            if existing is None:
                raise ConflictError("Concurrent request, please retry.",
                                    details={"key": key})
            if existing.request_hash != body_hash:
                raise IdempotencyError(
                    "Idempotency key reused with different request body.",
                    details={"key": key},
                )
            if existing.response_body is not None:
                response = jsonify(existing.response_body)
                response.status_code = existing.response_status or 200
                response.headers["X-Idempotent-Replay"] = "true"
                return response
            raise IdempotencyInFlightError(
                "Request is already in progress.",
                details={"key": key},
            )

        result = fn(*args, **kwargs)
        body, status = (result[0], result[1]) if isinstance(result, tuple) else (result, 200)

        record.status = "completed"
        record.response_status = status
        try:
            record.response_body = body.get_json() if hasattr(body, "get_json") else body
        except Exception:
            record.response_body = None
        db.session.commit()

        if redis_client is not None:
            try:
                redis_client.setex(
                    _redis_key(scope, key),
                    current_app.config.get("IDEMPOTENCY_TTL_SECONDS", 86400),
                    json.dumps({"status": status, "body": record.response_body}),
                )
            except Exception:
                pass

        return result
    return wrapper






import bleach
from markdown_it import MarkdownIt

_md = MarkdownIt("commonmark", {"html": False, "linkify": True, "typographer": True})
_md.enable("table").enable("strikethrough")

# Whitelist for sanitizing rendered HTML (and any raw HTML the client sends)
ALLOWED_TAGS = [
    "p", "br", "strong", "em", "u", "s", "code", "pre",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li", "blockquote",
    "a", "img",
    "table", "thead", "tbody", "tr", "th", "td",
    "hr", "figure", "figcaption",
]
ALLOWED_ATTRS = {
    "a": ["href", "title", "rel", "target"],
    "img": ["src", "alt", "title", "width", "height", "loading"],
    "code": ["class"],
    "pre": ["class"],
}


def render_markdown(md_text: str) -> str:
    """Markdown → sanitized HTML. Never returns raw user HTML."""
    if not md_text:
        return ""
    html = _md.render(md_text)
    return bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)


def sanitize_html(html: str) -> str:
    """For when the editor sends raw HTML. Strip everything dangerous."""
    if not html:
        return ""
    return bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)



