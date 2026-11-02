import hashlib, json
from app.models import AuditLog
from flask import g, request
from app import db

def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)

def _hash(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def _last_audit_hash() -> str | None:
    row = (
        AuditLog.query
        .order_by(AuditLog.created_at.desc())
        .limit(1)
        .first()
    )
    return row.row_hash if row else None


def write_audit(action, entity_type=None, entity_id=None,
                before=None, after=None, actor_type="user"):
    from flask import has_request_context

    actor_id = getattr(getattr(g, "current_user", None), "id", None)

    ip = ua = rid = None
    if has_request_context():
        ip  = request.remote_addr
        ua  = request.headers.get("User-Agent")
        rid = request.headers.get("X-Request-ID")

    before_hash = _hash(_canonical(before)) if before is not None else None
    after_hash  = _hash(_canonical(after))  if after  is not None else None
    prev_hash   = _last_audit_hash()

    row = AuditLog(
        actor_user_id=actor_id,
        actor_type=actor_type,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id else None,
        before=before,
        after=after,
        before_hash=before_hash,
        after_hash=after_hash,
        prev_hash=prev_hash,
        ip_address=ip,
        user_agent=ua,
        request_id=rid,
    )

    # Row hash includes the chain
    payload = {
        "action": action,
        "entity_type": entity_type,
        "entity_id": str(entity_id) if entity_id else None,
        "actor_user_id": str(actor_id) if actor_id else None,
        "actor_type": actor_type,
        "before_hash": before_hash,
        "after_hash": after_hash,
        "prev_hash": prev_hash,
        "request_id": rid,
    }
    row.row_hash = _hash(_canonical(payload))

    db.session.add(row)
    # caller commits


def verify_audit_chain(*, limit=None) -> dict:
    q = AuditLog.query.order_by(AuditLog.created_at.asc())
    if limit:
        q = q.limit(limit)
    prev = None
    checked = 0
    for row in q:
        if row.prev_hash != prev:
            return {"ok": False, "broken_at": str(row.id),
                    "expected_prev": prev, "found_prev": row.prev_hash}
        prev = row.row_hash
        checked += 1
    return {"ok": True, "checked": checked}