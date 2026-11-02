# services.py
from structlog import get_logger

from app import db


from app.models import Permission, Role, User, RoleAssignment
from app.models import ( TimelineEvent, TimelineEventType, )
from app.models import ( TimelineEvent, TimelineEventType,  utcnow, )
from app.models import ( TimelineEvent, TimelineEventType, utcnow, )


from app.models import User, Role, Permission
from app.security import hash_password, verify_password, issue_tokens


from datetime import datetime, timezone, timedelta, date
# from app.realtime import _safe_emit  # if you have it; else define below
from app.realtime import emit_alert, emit_to_user, ROOM_ADMINS, ROOM_SALES, ROOM_OPS, ROOM_ALL


from app.seeds import PERMISSIONS, DEFAULT_ROLES

log = get_logger("app.services")



IDEMPOTENCY_TTL = timedelta(hours=24)
IDEMPOTENT_METHODS = {"POST", "PATCH", "PUT", "DELETE"}



from app import db
from app.models import (
    TimelineEvent, TimelineEventType,
)


import hashlib
from functools import wraps
from datetime import timedelta
from flask import request, g, jsonify
from app import db
from app.models import IdempotencyKey, utcnow
from app.errors import IdempotencyError, IdempotencyInFlightError

IDEMPOTENCY_TTL = timedelta(hours=24)
IDEMPOTENT_METHODS = {"POST", "PATCH", "PUT", "DELETE"}

def _body_hash() -> str:
    raw = request.get_data(as_text=True) or ""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def _scope() -> str:
    user_id = getattr(g, "current_user", None)
    user_id = getattr(user_id, "id", "anonymous")
    return f"user:{user_id}:endpoint:{request.method}:{request.path}"

def idempotent(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        key = request.headers.get("Idempotency-Key")
        if not key or request.method not in IDEMPOTENT_METHODS:
            return fn(*args, **kwargs)

        scope = _scope()
        body_hash = _body_hash()

        existing = IdempotencyKey.query.filter_by(scope=scope, key=key).first()
        if existing and existing.expires_at < utcnow():
            db.session.delete(existing); db.session.commit()
            existing = None

        if existing:
            if existing.request_hash != body_hash:
                raise IdempotencyError(
                    "This idempotency key was used with a different request body.",
                    details={"original_request_hash": existing.request_hash,
                             "received_request_hash": body_hash},
                )
            if existing.status == "processing":
                raise IdempotencyInFlightError(
                    "A request with this key is still processing."
                )
            return jsonify(existing.response_body), existing.response_status or 200

        record = IdempotencyKey(
            key=key, scope=scope, request_hash=body_hash,
            status="processing",
            expires_at=utcnow() + IDEMPOTENCY_TTL,
        )
        db.session.add(record); db.session.commit()
        g._idempotency_record_id = record.id

        response = fn(*args, **kwargs)

        # response is (jsonify_result, status) from ok()/error()
        try:
            payload, status = response
        except (TypeError, ValueError):
            return response

        rec = db.session.get(IdempotencyKey, g._idempotency_record_id)
        if rec:
            rec.status = "completed"
            rec.response_status = status
            rec.response_body = payload.get_json()
            db.session.commit()
        return response
    return wrapper









# ─── Auth ───────────────────────────────────────────────────────────
from app.security import hash_password, verify_password, issue_tokens


def authenticate(email: str, password: str) -> dict | None:
    """
    Verify credentials. Returns {'user': User, 'tokens': {...}} on success,
    None on invalid credentials or inactive account.
    """
    if not email or not password:
        return None

    user = User.query.filter(
        db.func.lower(User.email) == email.lower()
    ).first()

    if not user or not user.is_active:
        return None

    # NOTE argument order: (plain, hash) — matches security.verify_password
    if not verify_password(password, user.password_hash):
        return None

    user.last_login_at = utcnow()
    db.session.flush()

    return {
        "user": user,
        "tokens": issue_tokens(user.id),
    }

# ─── Users ──────────────────────────────────────────────────────────



def list_users(limit: int = 100) -> list[User]:
    return (
        User.query
        .order_by(User.created_at.desc())
        .limit(min(limit, 500))
        .all()
    )


def get_user(user_id) -> User | None:
    return User.query.get(user_id)


def create_user(data: dict) -> User:
    """
    data: {email, full_name, phone?, password, is_active?}
    Raises ValueError on duplicate email.
    """
    email = data["email"].strip().lower()

    if User.query.filter(db.func.lower(User.email) == email).first():
        raise ValueError("A user with that email already exists.")

    user = User(
        email=email,
        full_name=data["full_name"],
        phone=data.get("phone"),
        password_hash=hash_password(data["password"]),
        is_active=data.get("is_active", True),
        is_verified=False,
    )
    db.session.add(user)
    db.session.flush()
    return user


def update_user(user: User, data: dict) -> User:
    if "full_name" in data:
        user.full_name = data["full_name"]
    if "phone" in data:
        user.phone = data["phone"]
    if "is_active" in data:
        user.is_active = data["is_active"]
    if data.get("password"):
        user.password_hash = hash_password(data["password"])
        user.token_version = (user.token_version or 0) + 1
    db.session.flush()
    return user


def deactivate_user(user: User) -> User:
    user.is_active = False
    user.token_version = (user.token_version or 0) + 1
    db.session.flush()
    return user


# ─── Roles ──────────────────────────────────────────────────────────

def list_roles() -> list[Role]:
    return Role.query.order_by(Role.name.asc()).all()


def get_role(role_id) -> Role | None:
    return Role.query.get(role_id)


def create_role(data: dict, *, actor_user_id=None) -> Role:
    """
    data: {name, slug, description?, permission_codes: [...]}
    """
    slug = data["slug"].strip().lower()
    if Role.query.filter_by(slug=slug).first():
        raise ValueError("A role with that slug already exists.")

    role = Role(
        name=data["name"],
        slug=slug,
        description=data.get("description"),
        is_system=False,
        is_protected=False,
    )
    db.session.add(role)
    db.session.flush()

    _sync_role_permissions(role, data.get("permission_codes", []))
    return role


def update_role(role: Role, data: dict, *, actor_user_id=None) -> Role:
    if role.is_protected and data.get("permission_codes") is not None:
        # protected roles can be renamed/described, but their permission set is locked
        raise ValueError("This role is protected; its permissions cannot be changed.")

    if "name" in data:
        role.name = data["name"]
    if "description" in data:
        role.description = data["description"]
    if data.get("permission_codes") is not None:
        _sync_role_permissions(role, data["permission_codes"])
    db.session.flush()
    return role
 

def delete_role(role: Role) -> None:
    if role.is_system or role.is_protected:
        raise ValueError("System and protected roles cannot be deleted.")
    if role.assignments:
        raise ValueError("Cannot delete a role that is assigned to users.")
    db.session.delete(role)
    db.session.flush()


def _sync_role_permissions(role: Role, permission_codes: list[str]) -> None:
    """Full replace: the given codes become the role's entire permission set."""
    if not permission_codes:
        role.permissions = []
        return

    perms = Permission.query.filter(Permission.code.in_(permission_codes)).all()
    found = {p.code for p in perms}
    missing = set(permission_codes) - found
    if missing:
        raise ValueError(f"Unknown permission code(s): {sorted(missing)}")

    role.permissions = perms


def seed_all():
    """Idempotent. Run from app factory or CLI."""
    # Permissions
    existing = {p.code: p for p in Permission.query.all()}
    for code, desc, cat in PERMISSIONS:
        if code not in existing:
            db.session.add(Permission(code=code, description=desc, category=cat))
    db.session.flush()

    perms_by_code = {p.code: p for p in Permission.query.all()}

    # Roles
    for slug, spec in DEFAULT_ROLES.items():
        role = Role.query.filter_by(slug=slug).first()
        if not role:
            role = Role(
                name=spec["name"], slug=slug,
                description=spec["description"],
                is_system=spec["is_system"],
                is_protected=spec["is_protected"],
            )
            db.session.add(role)
            db.session.flush()

        if spec["permissions"] == "*":
            role.permissions = list(perms_by_code.values())
        else:
            role.permissions = [perms_by_code[c] for c in spec["permissions"] if c in perms_by_code]

    db.session.commit()


from app.models import (
    TimelineEvent, TimelineEventType,
)
from sqlalchemy import or_, func

def normalize_phone(raw: str | None) -> str | None:
    """Kenya-focused E.164 normalizer. Returns +254XXXXXXXXX or None."""
    if not raw:
        return None
    digits = "".join(c for c in raw if c.isdigit() or c == "+")
    if digits.startswith("+"):
        return digits
    if digits.startswith("254"):
        return "+" + digits
    if digits.startswith("0"):
        return "+254" + digits[1:]
    if len(digits) == 9:
        return "+254" + digits
    return digits or None



from app.models import TimelineEvent, TimelineEventType


# ─── Phase 8: canonical timeline writer ─────────────────────────────

_VALID_EVENT_TYPES = frozenset(e.value for e in TimelineEventType)

def record_event(
    *,
    entity_type: str,
    entity_id,
    event_type,
    actor_user_id=None,
    actor_type: str | None = None,
    summary: str | None = None,
    metadata: dict | None = None,
    occurred_at=None,
) -> TimelineEvent:
    """
    The single sanctioned way to append a timeline event.

    - Validates event_type against TimelineEventType (typos are rejected).
    - Derives actor_type from actor_user_id unless overridden.
    - Does NOT commit — the caller owns the transaction.

    entity_type: 'enquiry' | 'booking' | 'quote' | 'invoice' | 'customer'
                 (or any new scoped entity you add later)
    event_type:  a TimelineEventType member OR its .value string
    """
    # Resolve event_type value
    if isinstance(event_type, TimelineEventType):
        evt_value = event_type.value
    elif isinstance(event_type, str):
        if event_type not in _VALID_EVENT_TYPES:
            raise ValueError(f"Unknown timeline event_type: {event_type!r}")
        evt_value = event_type
    else:
        raise TypeError("event_type must be TimelineEventType or str")

    # Derive actor_type if not given
    if actor_type is None:
        actor_type = "user" if actor_user_id else "system"

    event = TimelineEvent(
        entity_type=entity_type,
        entity_id=entity_id,
        event_type=evt_value,
        actor_type=actor_type,
        actor_user_id=actor_user_id,
        summary=summary,
        metadata_json=metadata or {},
        created_at=occurred_at or utcnow(),
    )
    db.session.add(event)
    db.session.flush()
    return event



from urllib.parse import quote


# ─── Phase 10: wa.me deep links ─────────────────────────────────────

def build_wa_link(
    *,
    phone: str,
    message: str,
    source_ref: str | None = None,
) -> str:
    """
    Build a wa.me deep link with a prefilled, URL-encoded message.

    phone: E.164 digits without '+', e.g. "254........."
    message: plain text; will be URL-encoded
    source_ref: optional tracking tag appended to the message as a hidden marker

    Returns: "https://wa.me/254.......?text=..."

    Does not require WhatsApp Business API, Meta approval, or a token.
    """
    # Normalize phone: strip everything except digits
    digits = "".join(ch for ch in str(phone) if ch.isdigit())
    if not digits:
        raise ValueError("Phone number must contain digits.")

    text = message
    if source_ref:
        text = f"{text}\n\n[ref: {source_ref}]"

    return f"https://wa.me/{digits}?text={quote(text)}"

# Context-aware builders — used by the API and the frontend

def wa_link_for_package(package_name: str, phone: str, *, source_ref=None) -> str:
    return build_wa_link(
        phone=phone,
        message=(
            f"Hello Funworld Events! I'm interested in the {package_name} package. "
            "Could you share pricing and availability?"
        ),
        source_ref=source_ref or "package",
    )


def wa_link_for_service(service_name: str, phone: str, *, source_ref=None) -> str:
    return build_wa_link(
        phone=phone,
        message=(
            f"Hello Funworld Events! I'd like to enquire about your {service_name} service. "
            "Please share details."
        ),
        source_ref=source_ref or "service",
    )





# ─── Phase 12: Blog ─────────────────────────────────────────────────

import math
import re
from datetime import datetime, timezone

from app.models import (
    BlogPost, BlogPostStatus, BlogCategory, BlogTag,
    BlogPostRevision, User,
)
from app.security import render_markdown


# ─── Slug generation ────────────────────────────────────────────────

def _slugify(text: str) -> str:
    """URL-safe slug. Keeps unicode letters (Swahili names work)."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text[:150]


def generate_unique_slug(base: str, *, exclude_post_id=None) -> str:
    slug = _slugify(base)
    if not slug:
        raise ValueError("Cannot generate slug from empty title.")
    candidate = slug
    i = 2
    while True:
        q = BlogPost.query.filter_by(slug=candidate)
        if exclude_post_id:
            q = q.filter(BlogPost.id != exclude_post_id)
        if not q.first():
            return candidate
        candidate = f"{slug}-{i}"
        i += 1


# ─── Reading time ───────────────────────────────────────────────────

def _estimate_reading_minutes(md_text: str) -> int:
    if not md_text:
        return 0
    words = len(re.findall(r"\w+", md_text))
    return max(1, math.ceil(words / 220))


# ─── Post creation ──────────────────────────────────────────────────

def create_blog_post(
    *,
    title: str,
    body_markdown: str = "",
    excerpt: str | None = None,
    featured_image_url: str | None = None,
    featured_image_alt: str | None = None,
    seo_title: str | None = None,
    seo_description: str | None = None,
    canonical_url: str | None = None,
    og_image_url: str | None = None,
    featured: bool = False,
    author_user_id=None,
    category_slugs: list[str] | None = None,
    tag_slugs: list[str] | None = None,
) -> BlogPost:

    


    slug = generate_unique_slug(title)
    post = BlogPost(
        slug=slug,
        title=title.strip(),
        excerpt=excerpt,
        body_markdown=body_markdown,
        body_html=render_markdown(body_markdown),
        featured_image_url=featured_image_url,
        featured_image_alt=featured_image_alt,
        seo_title=seo_title,
        seo_description=seo_description,
        canonical_url=canonical_url,
        og_image_url=og_image_url,
        featured=featured,
        author_user_id=author_user_id,
        status=BlogPostStatus.DRAFT,
        reading_minutes=_estimate_reading_minutes(body_markdown),
    )
    db.session.add(post)
    db.session.flush()

    if category_slugs:
        post.categories = _resolve_categories(category_slugs)
    if tag_slugs:
        post.tags = _resolve_tags(tag_slugs)

    _save_revision(post, author_user_id=author_user_id)
    db.session.flush()
    return post


def _resolve_categories(slugs: list[str]) -> list[BlogCategory]:
    if not slugs:
        return []
    return BlogCategory.query.filter(BlogCategory.slug.in_(slugs)).all()


def _resolve_tags(slugs: list[str]) -> list[BlogTag]:
    if not slugs:
        return []
    return BlogTag.query.filter(BlogTag.slug.in_(slugs)).all()


def _save_revision(post: BlogPost, *, author_user_id=None):
    """Append a revision. Numbered per post, monotonic."""
    last = (
        BlogPostRevision.query
        .filter_by(post_id=post.id)
        .order_by(BlogPostRevision.revision_number.desc())
        .first()
    )
    next_num = (last.revision_number + 1) if last else 1
    db.session.add(BlogPostRevision(
        post_id=post.id,
        revision_number=next_num,
        title=post.title,
        body_markdown=post.body_markdown,
        saved_by_user_id=author_user_id,
    ))


# ─── Post update ────────────────────────────────────────────────────

def update_blog_post(
    post: BlogPost,
    *,
    data: dict,
    author_user_id=None,
) -> BlogPost:
    """
    Apply a partial update. Only writes fields present in `data`.
    Never allows slug change on a published post.
    """
    if "title" in data and data["title"] != post.title:
        post.title = data["title"].strip()
        # Allow slug change only if not yet published
        if post.status in (BlogPostStatus.DRAFT, BlogPostStatus.REVIEW):
            post.slug = generate_unique_slug(post.title, exclude_post_id=post.id)

    if "body_markdown" in data:
        post.body_markdown = data["body_markdown"]
        post.body_html = render_markdown(data["body_markdown"])
        post.reading_minutes = _estimate_reading_minutes(data["body_markdown"])

    for field in ("excerpt", "featured_image_url", "featured_image_alt",
                  "seo_title", "seo_description", "canonical_url",
                  "og_image_url"):
        if field in data:
            setattr(post, field, data[field])

    if "category_slugs" in data:
        post.categories = _resolve_categories(data["category_slugs"] or [])
    if "tag_slugs" in data:
        post.tags = _resolve_tags(data["tag_slugs"] or [])

    if "featured" in data:
        post.featured = bool(data["featured"])

    _save_revision(post, author_user_id=author_user_id)
    db.session.flush()
    return post


# ─── Workflow transitions ───────────────────────────────────────────

def submit_post_for_review(post: BlogPost, *, actor_user_id):
    if post.status not in (BlogPostStatus.DRAFT, BlogPostStatus.REJECTED):
        raise ValueError("Only draft or rejected posts can be submitted for review.")
    post.status = BlogPostStatus.REVIEW
    post.submitted_for_review_at = utcnow()
    post.rejection_reason = None
    record_event(
        entity_type="blog_post", entity_id=post.id,
        event_type="blog_post.submitted",
        actor_user_id=actor_user_id,
        summary=f"Submitted for review: {post.title}",
    )
    db.session.flush()
    return post


def approve_post(post: BlogPost, *, actor_user_id):
    if post.status != BlogPostStatus.REVIEW:
        raise ValueError("Only posts in review can be approved.")
    post.status = BlogPostStatus.SCHEDULED  # moved here; publish sets timestamp
    post.reviewed_by_user_id = actor_user_id
    post.reviewed_at = utcnow()
    if not post.scheduled_for:
        post.scheduled_for = utcnow()  # publish immediately on next tick
    record_event(
        entity_type="blog_post", entity_id=post.id,
        event_type="blog_post.approved",
        actor_user_id=actor_user_id,
        summary=f"Approved: {post.title}",
    )
    db.session.flush()
    return post


def reject_post(post: BlogPost, *, reason: str, actor_user_id):
    if post.status != BlogPostStatus.REVIEW:
        raise ValueError("Only posts in review can be rejected.")
    post.status = BlogPostStatus.REJECTED
    post.rejection_reason = reason
    post.reviewed_by_user_id = actor_user_id
    post.reviewed_at = utcnow()
    record_event(
        entity_type="blog_post", entity_id=post.id,
        event_type="blog_post.rejected",
        actor_user_id=actor_user_id,
        summary=f"Rejected: {reason}",
    )
    db.session.flush()
    return post


def publish_post(post: BlogPost, *, actor_user_id):
    if post.status not in (BlogPostStatus.SCHEDULED, BlogPostStatus.DRAFT):
        raise ValueError("Only scheduled or draft posts can be published.")
    post.status = BlogPostStatus.PUBLISHED
    post.published_at = utcnow()
    record_event(
        entity_type="blog_post", entity_id=post.id,
        event_type="blog_post.published",
        actor_user_id=actor_user_id,
        summary=f"Published: {post.title}",
        metadata={"slug": post.slug},
    )
    db.session.flush()
    return post


def archive_post(post: BlogPost, *, actor_user_id):
    if post.status == BlogPostStatus.ARCHIVED:
        return post
    post.status = BlogPostStatus.ARCHIVED
    post.archived_at = utcnow()
    record_event(
        entity_type="blog_post", entity_id=post.id,
        event_type="blog_post.archived",
        actor_user_id=actor_user_id,
        summary=f"Archived: {post.title}",
    )
    db.session.flush()
    return post


def publish_due_scheduled_posts(*, now=None) -> int:
    """Scheduler hook. Publishes any SCHEDULED posts whose scheduled_for has passed."""
    now = now or utcnow()
    due = BlogPost.query.filter(
        BlogPost.status == BlogPostStatus.SCHEDULED,
        BlogPost.scheduled_for.isnot(None),
        BlogPost.scheduled_for <= now,
    ).all()
    for post in due:
        post.status = BlogPostStatus.PUBLISHED
        post.published_at = utcnow()
        record_event(
            entity_type="blog_post", entity_id=post.id,
            event_type="blog_post.published",
            actor_type="system",
            summary=f"Auto-published: {post.title}",
        )
    if due:
        db.session.commit()
    return len(due)


# ─── Public query helpers ───────────────────────────────────────────

def list_published_posts(
    *,
    category_slug: str | None = None,
    tag_slug: str | None = None,
    author_id=None,
    limit: int = 20,
    offset: int = 0,
    featured_only: bool = False,
):
    q = BlogPost.query.filter(
        BlogPost.status == BlogPostStatus.PUBLISHED,
        BlogPost.published_at <= utcnow(),
    )

    if category_slug:
        q = q.join(BlogPost.categories).filter(BlogCategory.slug == category_slug)
    if tag_slug:
        q = q.join(BlogPost.tags).filter(BlogTag.slug == tag_slug)
    if author_id:
        q = q.filter(BlogPost.author_user_id == author_id)
    if featured_only:
        q = q.filter(BlogPost.featured.is_(True))

    total = q.count()
    posts = (
        q.order_by(BlogPost.published_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    return posts, total


def get_published_post(slug: str) -> BlogPost | None:
    post = BlogPost.query.filter_by(slug=slug).first()
    if not post:
        return None
    if post.status != BlogPostStatus.PUBLISHED:
        return None
    if post.published_at and post.published_at > utcnow():
        return None
    return post


def increment_post_views(post: BlogPost):
    """Best-effort view counter. Caller commits."""
    post.view_count = (post.view_count or 0) + 1
    db.session.flush()


# ─── Internal link suggestions ──────────────────────────────────────

def suggest_internal_links(text: str, *, limit: int = 5) -> list[dict]:
    """
    Naive keyword matching against service / package / blog titles.
    Returns candidates the editor can insert manually.
    Lowercased substring match, ranked by longest match.
    """
    if not text:
        return []

    haystack = text.lower()
    candidates: list[tuple[int, dict]] = []

    # Services (hardcoded for now; move to a Service table later)
    for name, url in [
        ("wedding planning", "/services/weddings"),
        ("corporate event", "/services/corporate"),
        ("kids party", "/services/kids"),
        ("kids parties", "/services/kids"),
        ("school funday", "/services/school-fundays"),
        ("school fundays", "/services/school-fundays"),
    ]:
        if name in haystack:
            candidates.append((len(name), {"label": name.title(), "url": url}))

    # Existing published blog posts
    for p in BlogPost.query.filter_by(status=BlogPostStatus.PUBLISHED).limit(50).all():
        if p.title.lower() in haystack or p.slug.replace("-", " ") in haystack:
            candidates.append((len(p.title), {"label": p.title, "url": f"/blog/{p.slug}"}))

    candidates.sort(reverse=True, key=lambda x: x[0])
    seen = set()
    out = []
    for _, c in candidates:
        if c["url"] in seen:
            continue
        seen.add(c["url"])
        out.append(c)
        if len(out) >= limit:
            break
    return out




from app.models import (
    ServiceCategory, Service, Package, PackageStatus,
)


# ─── Services ────────────────────────────────────────────────────────

def _slugify_short(text: str, max_len: int = 120) -> str:
    import re
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")[:max_len]


def list_published_services(*, category_slug: str | None = None,
                             limit: int = 200):
    q = Service.query.filter(Service.is_published.is_(True))
    if category_slug:
        q = q.join(ServiceCategory).filter(ServiceCategory.slug == category_slug)
    return q.order_by(Service.sort_order.asc(), Service.name.asc()).limit(limit).all()


def get_published_service(category_slug: str, service_slug: str) -> Service | None:
    return (
        Service.query
        .join(ServiceCategory)
        .filter(
            ServiceCategory.slug == category_slug,
            Service.slug == service_slug,
            Service.is_published.is_(True),
        )
        .first()
    )


def create_service(*, category_id, name, **kwargs) -> Service:
    slug = kwargs.pop("slug", None) or _slugify_short(name)
    existing = Service.query.filter_by(category_id=category_id, slug=slug).first()
    if existing:
        raise ValueError(f"A service with slug '{slug}' already exists in this category.")
    svc = Service(category_id=category_id, slug=slug, name=name, **kwargs)
    db.session.add(svc)
    db.session.flush()
    return svc


def update_service(service: Service, *, data: dict) -> Service:
    for field in (
        "name", "short_description", "long_description",
        "featured_image_url", "gallery", "price_note", "tags",
        "sort_order", "seo_title", "seo_description",
    ):
        if field in data:
            setattr(service, field, data[field])
    db.session.flush()
    return service


def publish_service(service: Service, *, actor_user_id):
    service.is_published = True
    service.published_at = utcnow()
    record_event(
        entity_type="service", entity_id=service.id,
        event_type="service.published",
        actor_user_id=actor_user_id,
        summary=f"Published: {service.name}",
    )
    db.session.flush()
    return service


def unpublish_service(service: Service, *, actor_user_id):
    service.is_published = False
    record_event(
        entity_type="service", entity_id=service.id,
        event_type="service.unpublished",
        actor_user_id=actor_user_id,
        summary=f"Unpublished: {service.name}",
    )
    db.session.flush()
    return service


# ─── Packages ────────────────────────────────────────────────────────

def _slugify_package(text: str) -> str:
    return _slugify_short(text, max_len=140)


def create_package(*, name, created_by_user_id, **kwargs) -> Package:
    name = (name or "").strip()
    if not name:
        raise ValueError("Package name is required.")

    slug = kwargs.pop("slug", None) or _slugify_package(name)
    if Package.query.filter_by(slug=slug).first():
        raise ValueError(f"A package with slug '{slug}' already exists.")
    pkg = Package(
        slug=slug, name=name,
        status=PackageStatus.DRAFT,
        created_by_user_id=created_by_user_id,
        **kwargs,
    )
    db.session.add(pkg)
    db.session.flush()
    record_event(
        entity_type="package", entity_id=pkg.id,
        event_type="package.created",
        actor_user_id=created_by_user_id,
        summary=f"Package created: {pkg.name}",
    )
    return pkg


def update_package(pkg: Package, *, data: dict) -> Package:
    # Allow editing in DRAFT, REJECTED, and PUBLISHED (with a note)
    if pkg.status == PackageStatus.PENDING_REVIEW:
        raise ValueError("Cannot edit a package while it is under review.")
    for field in (
        "name", "tagline", "short_description", "long_description",
        "what_is_included", "what_is_not_included",
        "hero_image_url", "gallery", "category_id",
        "price_amount", "price_note", "currency",
        "min_guests", "max_guests", "duration_hours", "availability_note",
        "is_featured", "seo_title", "seo_description",
    ):
        if field in data:
            setattr(pkg, field, data[field])
    db.session.flush()
    return pkg


def submit_package_for_review(pkg: Package, *, actor_user_id):
    if pkg.status not in (PackageStatus.DRAFT, PackageStatus.REJECTED):
        raise ValueError("Only draft or rejected packages can be submitted.")
    pkg.status = PackageStatus.PENDING_REVIEW
    pkg.submitted_at = utcnow()
    pkg.rejection_reason = None
    record_event(
        entity_type="package", entity_id=pkg.id,
        event_type="package.submitted",
        actor_user_id=actor_user_id,
        summary=f"Submitted for review: {pkg.name}",
    )
    db.session.flush()
    return pkg


def approve_package(pkg: Package, *, actor_user_id):
    """Owner-only. Moves to PUBLISHED in one step."""
    if pkg.status != PackageStatus.PENDING_REVIEW:
        raise ValueError("Only packages under review can be approved.")
    pkg.status = PackageStatus.PUBLISHED
    pkg.reviewed_by_user_id = actor_user_id
    pkg.reviewed_at = utcnow()
    pkg.published_at = utcnow()
    record_event(
        entity_type="package", entity_id=pkg.id,
        event_type="package.published",
        actor_user_id=actor_user_id,
        summary=f"Approved & published: {pkg.name}",
    )
    db.session.flush()
    return pkg


def reject_package(pkg: Package, *, reason: str, actor_user_id):
    if pkg.status != PackageStatus.PENDING_REVIEW:
        raise ValueError("Only packages under review can be rejected.")
    pkg.status = PackageStatus.REJECTED
    pkg.rejection_reason = reason
    pkg.reviewed_by_user_id = actor_user_id
    pkg.reviewed_at = utcnow()
    record_event(
        entity_type="package", entity_id=pkg.id,
        event_type="package.rejected",
        actor_user_id=actor_user_id,
        summary=f"Rejected: {reason}",
    )
    db.session.flush()
    return pkg


def unpublish_package(pkg: Package, *, actor_user_id):
    if pkg.status != PackageStatus.PUBLISHED:
        raise ValueError("Only published packages can be unpublished.")
    pkg.status = PackageStatus.DRAFT
    record_event(
        entity_type="package", entity_id=pkg.id,
        event_type="package.unpublished",
        actor_user_id=actor_user_id,
        summary=f"Unpublished: {pkg.name}",
    )
    db.session.flush()
    return pkg


def archive_package(pkg: Package, *, actor_user_id):
    pkg.status = PackageStatus.ARCHIVED
    pkg.archived_at = utcnow()
    record_event(
        entity_type="package", entity_id=pkg.id,
        event_type="package.archived",
        actor_user_id=actor_user_id,
        summary=f"Archived: {pkg.name}",
    )
    db.session.flush()
    return pkg


def list_published_packages(*, category_slug=None, featured_only=False, limit=100):
    q = Package.query.filter(Package.status == PackageStatus.PUBLISHED)
    if category_slug:
        q = q.join(ServiceCategory).filter(ServiceCategory.slug == category_slug)
    if featured_only:
        q = q.filter(Package.is_featured.is_(True))
    return q.order_by(Package.published_at.desc()).limit(limit).all()


def get_published_package(slug: str) -> Package | None:
    return Package.query.filter_by(slug=slug, status=PackageStatus.PUBLISHED).first()





from app.models import (
    InventoryCategory, InventoryItem,
    PackageInventoryItem,
)


# ─── Inventory categories ───────────────────────────────────────────

def list_inventory_categories(*, include_inactive=True):
    q = InventoryCategory.query
    return q.order_by(InventoryCategory.sort_order.asc()).all()


def create_inventory_category(*, slug, name, **kwargs) -> InventoryCategory:
    slug = (slug or "").strip().lower()
    if not slug:
        raise ValueError("Slug is required.")
    if InventoryCategory.query.filter_by(slug=slug).first():
        raise ValueError(f"Category slug '{slug}' already exists.")
    cat = InventoryCategory(slug=slug, name=name, **kwargs)
    db.session.add(cat)
    db.session.flush()
    return cat


def update_inventory_category(cat: InventoryCategory, *, data: dict) -> InventoryCategory:
    for field in ("name", "short_description", "long_description",
                  "icon", "sort_order", "seo_title", "seo_description"):
        if field in data:
            setattr(cat, field, data[field])
    db.session.flush()
    return cat


# ─── Inventory items ────────────────────────────────────────────────

def _slugify_item(text: str) -> str:
    import re
    text = (text or "").lower().strip()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")[:140]


def list_inventory_items(*, category_id=None, published_only=False, search=None):
    q = InventoryItem.query
    if category_id:
        q = q.filter(InventoryItem.category_id == category_id)
    if published_only:
        q = q.filter(InventoryItem.is_published.is_(True))
    if search:
        like = f"%{search}%"
        q = q.filter(InventoryItem.name.ilike(like))
    return q.order_by(InventoryItem.sort_order.asc(), InventoryItem.name.asc()).all()


def create_inventory_item(*, category_id, name, **kwargs) -> InventoryItem:
    name = (name or "").strip()
    if len(name) < 2:
        raise ValueError("Item name must be at least 2 characters.")

    slug = kwargs.pop("slug", None) or _slugify_item(name)
    if not slug:
        raise ValueError("Could not generate slug from name.")

    if InventoryItem.query.filter_by(category_id=category_id, slug=slug).first():
        raise ValueError(f"An item with slug '{slug}' already exists in this category.")

    item = InventoryItem(category_id=category_id, slug=slug, name=name, **kwargs)
    db.session.add(item)
    db.session.flush()
    return item


def update_inventory_item(item: InventoryItem, *, data: dict) -> InventoryItem:
    for field in (
        "name", "short_description", "long_description",
        "quantity_owned", "quantity_available_note",
        "unit_price_hint", "unit", "currency",
        "featured_image_url", "gallery", "tags",
        "sort_order", "seo_title", "seo_description",
    ):
        if field in data:
            setattr(item, field, data[field])
    db.session.flush()
    return item


def publish_inventory_item(item: InventoryItem, *, actor_user_id):
    item.is_published = True
    item.published_at = utcnow()
    record_event(
        entity_type="inventory_item", entity_id=item.id,
        event_type="inventory_item.published",
        actor_user_id=actor_user_id,
        summary=f"Published: {item.name}",
    )
    db.session.flush()
    return item


def unpublish_inventory_item(item: InventoryItem, *, actor_user_id):
    item.is_published = False
    record_event(
        entity_type="inventory_item", entity_id=item.id,
        event_type="inventory_item.unpublished",
        actor_user_id=actor_user_id,
        summary=f"Unpublished: {item.name}",
    )
    db.session.flush()
    return item


def delete_inventory_item(item: InventoryItem):
    db.session.delete(item)
    db.session.flush()


# ─── Link helpers ───────────────────────────────────────────────────

def _replace_link_items(parent_model, parent_id_field, parent_id,
                        line_items: list[dict], model_cls):
    """
    Generic replace: given a list of {inventory_item_id, quantity, notes},
    wipe existing links for the parent and recreate.
    """
    model_cls.query.filter_by(**{parent_id_field: parent_id}).delete()
    for i, row in enumerate(line_items):
        if not row.get("inventory_item_id"):
            continue
        db.session.add(model_cls(
            **{parent_id_field: parent_id},
            inventory_item_id=row["inventory_item_id"],
            quantity=max(1, int(row.get("quantity", 1))),
            notes=row.get("notes"),
        ))
    db.session.flush()


def set_package_inventory(package, items: list[dict]):
    """items: [{inventory_item_id, quantity, notes?, sort_order?}]"""
    PackageInventoryItem.query.filter_by(package_id=package.id).delete()
    for i, row in enumerate(items):
        if not row.get("inventory_item_id"):
            continue
        db.session.add(PackageInventoryItem(
            package_id=package.id,
            inventory_item_id=row["inventory_item_id"],
            quantity=max(1, int(row.get("quantity", 1))),
            notes=row.get("notes"),
            sort_order=row.get("sort_order", i),
        ))
    db.session.flush()





from app.models import GalleryAlbum, GalleryImage
from app.images import process_and_store_image, delete_image


def _slugify_gallery(text: str) -> str:
    import re
    text = (text or "").lower().strip()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")[:80]


# ─── Albums ─────────────────────────────────────────────────────────

def create_gallery_album(*, name, **kwargs) -> GalleryAlbum:
    name = (name or "").strip()
    if len(name) < 2:
        raise ValueError("Album name must be at least 2 characters.")
    slug = kwargs.pop("slug", None) or _slugify_gallery(name)
    if not slug:
        raise ValueError("Could not generate slug.")
    if GalleryAlbum.query.filter_by(slug=slug).first():
        raise ValueError(f"Album slug '{slug}' already exists.")
    album = GalleryAlbum(slug=slug, name=name, **kwargs)
    db.session.add(album)
    db.session.flush()
    return album


def update_gallery_album(album: GalleryAlbum, *, data: dict) -> GalleryAlbum:
    for field in ("name", "description", "category_id", "cover_image_url",
                  "sort_order", "seo_title", "seo_description"):
        if field in data:
            setattr(album, field, data[field])
    db.session.flush()
    return album


def publish_gallery_album(album: GalleryAlbum, *, actor_user_id):
    album.is_published = True
    album.published_at = utcnow()
    record_event(
        entity_type="gallery_album", entity_id=album.id,
        event_type="gallery_album.published",
        actor_user_id=actor_user_id,
        summary=f"Published album: {album.name}",
    )
    db.session.flush()
    return album


def unpublish_gallery_album(album: GalleryAlbum, *, actor_user_id):
    album.is_published = False
    record_event(
        entity_type="gallery_album", entity_id=album.id,
        event_type="gallery_album.unpublished",
        actor_user_id=actor_user_id,
        summary=f"Unpublished album: {album.name}",
    )
    db.session.flush()
    return album


def delete_gallery_album(album: GalleryAlbum):
    """Delete album AND its images (cascade). Also deletes stored files."""
    for img in album.images:
        try:
            delete_image(img.storage_key)
        except Exception:
            pass
    db.session.delete(album)
    db.session.flush()


# ─── Images ─────────────────────────────────────────────────────────

def create_gallery_image(
    *,
    file_bytes: bytes,
    mime_type: str,
    alt_text: str,
    caption: str | None = None,
    album_id=None,
    category_id=None,
    uploaded_by_user_id=None,
) -> GalleryImage:
    if not alt_text or not alt_text.strip():
        raise ValueError("Alt text is required for accessibility.")

    meta = process_and_store_image(
        file_bytes=file_bytes,
        mime_type=mime_type,
        prefix="gallery",
    )

    # Determine sort_order — append to end
    max_sort = (
        db.session.query(db.func.coalesce(db.func.max(GalleryImage.sort_order), 0))
        .filter_by(album_id=album_id)
        .scalar()
    )

    img = GalleryImage(
        album_id=album_id,
        category_id=category_id,
        storage_key=meta["key"],
        url=meta["url"],
        caption=caption,
        alt_text=alt_text.strip(),
        width=meta["width"],
        height=meta["height"],
        size_bytes=meta["size_bytes"],
        mime_type=meta["mime_type"],
        sort_order=(max_sort or 0) + 10,
        uploaded_by_user_id=uploaded_by_user_id,
    )
    db.session.add(img)
    db.session.flush()
    return img


def update_gallery_image(img: GalleryImage, *, data: dict) -> GalleryImage:
    for field in ("caption", "alt_text", "album_id", "category_id",
                  "sort_order", "is_featured"):
        if field in data:
            setattr(img, field, data[field])
    db.session.flush()
    return img


def publish_gallery_image(img: GalleryImage, *, actor_user_id):
    img.is_published = True
    img.published_at = utcnow()
    record_event(
        entity_type="gallery_image", entity_id=img.id,
        event_type="gallery_image.published",
        actor_user_id=actor_user_id,
        summary="Image published",
    )
    db.session.flush()
    return img


def unpublish_gallery_image(img: GalleryImage, *, actor_user_id):
    img.is_published = False
    record_event(
        entity_type="gallery_image", entity_id=img.id,
        event_type="gallery_image.unpublished",
        actor_user_id=actor_user_id,
        summary="Image unpublished",
    )
    db.session.flush()
    return img


def delete_gallery_image(img: GalleryImage):
    try:
        delete_image(img.storage_key)
    except Exception:
        pass
    db.session.delete(img)
    db.session.flush()


def reorder_gallery_images(order: list[tuple[str, int]]):
    """order: [(image_id, sort_order), ...]"""
    for image_id, sort in order:
        img = GalleryImage.query.get(image_id)
        if img:
            img.sort_order = int(sort)
    db.session.flush()


# ─── Public query helpers ───────────────────────────────────────────
def list_public_gallery(
    *,
    category_slug: str | None = None,
    album_slug: str | None = None,
    limit: int = 100,
    featured_only: bool = False,
):
    q = GalleryImage.query.filter(GalleryImage.is_published.is_(True))

    if featured_only:
        q = q.filter(GalleryImage.is_featured.is_(True))

    if album_slug:
        album = GalleryAlbum.query.filter_by(slug=album_slug).first()
        if album:
            q = q.filter(GalleryImage.album_id == album.id)
        else:
            return []
    elif category_slug:
        cat = ServiceCategory.query.filter_by(slug=category_slug).first()
        if cat:
            q = q.filter(
                (GalleryImage.category_id == cat.id)
                | (GalleryImage.album.has(GalleryAlbum.category_id == cat.id))
            )
        else:
            return []

    return q.order_by(GalleryImage.sort_order.asc()).limit(limit).all()

    





from app.models import Setting, SettingCategory, SettingRevision


# ─── Settings ───────────────────────────────────────────────────────

def get_setting(key: str) -> Setting | None:
    return Setting.query.filter_by(key=key).first()


def get_setting_value(key: str, default=None):
    s = get_setting(key)
    return s.value_text if s and s.is_published else default


def list_settings(*, category: SettingCategory | None = None):
    q = Setting.query
    if category:
        q = q.filter(Setting.category == category)
    return q.order_by(Setting.category.asc(), Setting.label.asc()).all()


def update_setting(setting: Setting, *, value_text: str | None,
                   label: str | None = None,
                   is_published: bool | None = None,
                   actor_user_id=None) -> Setting:
    # Snapshot the previous version
    if setting.value_text != value_text:
        db.session.add(SettingRevision(
            setting_id=setting.id,
            version=setting.version,
            value_text=setting.value_text,
            changed_by_user_id=actor_user_id,
        ))
        setting.version = (setting.version or 1) + 1
        setting.value_text = value_text

    if label is not None:
        setting.label = label
    if is_published is not None:
        setting.is_published = is_published

    setting.updated_by_user_id = actor_user_id
    db.session.flush()
    return setting


def create_setting(*, key, label, category, value_text=None,
                   description=None, is_system=False, actor_user_id=None) -> Setting:
    key = (key or "").strip().lower().replace(" ", "_")
    if not key:
        raise ValueError("Setting key is required.")
    if Setting.query.filter_by(key=key).first():
        raise ValueError(f"Setting '{key}' already exists.")
    s = Setting(
        key=key, label=label, category=category,
        value_text=value_text, description=description,
        is_system=is_system,
        updated_by_user_id=actor_user_id,
    )
    db.session.add(s)
    db.session.flush()
    return s








import hashlib
import requests as _http
from datetime import timedelta
from app.models import VisitorSession, PageView
from flask import current_app

# ─── Analytics ──────────────────────────────────────────────────────

SESSION_TTL_MINUTES = 30


def _hash_ip(ip: str) -> str:
    salt = current_app.config.get("SECRET_KEY", "dev")
    return hashlib.sha256(f"{salt}:{ip}".encode("utf-8")).hexdigest()[:32]


def _geolocate(ip: str) -> dict:
    """
    Look up geo data for an IP. Returns dict with country/region/city/isp.
    Free-tier ip-api.com. Never raises — returns empty on failure.
    """
    if not ip or ip.startswith(("127.", "10.", "192.168.", "172.")):
        return {}
    try:
        r = _http.get(
            f"http://ip-api.com/json/{ip}",
            params={"fields": "status,country,regionName,city,timezone,isp"},
            timeout=2,
        )
        if r.status_code != 200:
            return {}
        data = r.json()
        if data.get("status") != "success":
            return {}
        return {
            "country": data.get("country"),
            "region": data.get("regionName"),
            "city": data.get("city"),
            "timezone": data.get("timezone"),
            "isp": data.get("isp"),
        }
    except Exception:
        return {}


def track_page_view(*, session_id, path, referrer, ip, user_agent,
                    user_id=None) -> tuple[VisitorSession, PageView]:
    """
    Record a page view. Updates the session's last_seen and page_count.
    If the session is new or expired, creates a new VisitorSession.
    """
    now = utcnow()

    session = VisitorSession.query.filter_by(session_id=session_id).first()
    if session and (now - session.last_seen_at) > timedelta(minutes=SESSION_TTL_MINUTES):
        # Session expired — reset
        session.first_seen_at = now
        session.page_count = 0

    if not session:
        geo = _geolocate(ip)
        session = VisitorSession(
            session_id=session_id,
            ip_hash=_hash_ip(ip) if ip else None,
            country=geo.get("country"),
            region=geo.get("region"),
            city=geo.get("city"),
            timezone=geo.get("timezone"),
            isp=geo.get("isp"),
            referrer=referrer,
            user_agent=user_agent,
            user_id=user_id,
            first_seen_at=now,
            last_seen_at=now,
        )
        db.session.add(session)
    else:
        session.last_seen_at = now
        if user_id and not session.user_id:
            session.user_id = user_id

    session.page_count = (session.page_count or 0) + 1

    view = PageView(
        session_id=session_id,
        path=path[:500],
        referrer=referrer[:500] if referrer else None,
        country=session.country,
        city=session.city,
        user_id=user_id,
        created_at=now,
    )
    db.session.add(view)
    db.session.flush()
    return session, view


def analytics_overview(*, days=30) -> dict:
    """Aggregated stats for the dashboard."""
    from sqlalchemy import func
    since = utcnow() - timedelta(days=days)

    total_views = PageView.query.filter(PageView.created_at >= since).count()
    total_sessions = VisitorSession.query.filter(
        VisitorSession.first_seen_at >= since
    ).count()
    converted = VisitorSession.query.filter(
        VisitorSession.first_seen_at >= since,
    ).count()
    conversion_rate = round(converted / total_sessions, 3) if total_sessions else 0

    top_pages = db.session.query(
        PageView.path,
        func.count(PageView.id).label("views"),
    ).filter(PageView.created_at >= since).group_by(PageView.path)\
        .order_by(func.count(PageView.id).desc()).limit(20).all()

    top_countries = db.session.query(
        PageView.country,
        func.count(PageView.id).label("views"),
    ).filter(PageView.created_at >= since, PageView.country.isnot(None))\
        .group_by(PageView.country)\
        .order_by(func.count(PageView.id).desc()).limit(20).all()

    top_cities = db.session.query(
        PageView.city,
        func.count(PageView.id).label("views"),
    ).filter(PageView.created_at >= since, PageView.city.isnot(None))\
        .group_by(PageView.city)\
        .order_by(func.count(PageView.id).desc()).limit(20).all()

    daily = db.session.query(
        func.date_trunc("day", PageView.created_at).label("day"),
        func.count(PageView.id).label("views"),
    ).filter(PageView.created_at >= since)\
        .group_by("day").order_by("day").all()

    return {
        "range_days": days,
        "total_views": total_views,
        "total_sessions": total_sessions,
        "converted_sessions": converted,
        "conversion_rate": conversion_rate,
        "top_pages": [{"path": p, "views": v} for p, v in top_pages],
        "top_countries": [{"country": c or "Unknown", "views": v} for c, v in top_countries],
        "top_cities": [{"city": c, "views": v} for c, v in top_cities],
        "daily": [{"date": d.isoformat(), "views": v} for d, v in daily],
    }











def wa_link_for_rental_item(item_name: str, phone: str, *, source_ref=None,
                            category_name: str | None = None) -> str:
    """
    Prefilled message for a rental (inventory) item enquiry.
    Kept deliberately short so the customer can append date/venue.
    """
    subject = f"{item_name}"
    if category_name:
        subject = f"{item_name} ({category_name})"

    return build_wa_link(
        phone=phone,
        message=(
            f"Hello Funworld Events! I'd like to hire the {subject}. "
            "Could you confirm availability and pricing for my event date?"
        ),
        source_ref=source_ref or "rental_item",
    )

def get_public_whatsapp_phone() -> str | None:
    """
    Returns digits-only E.164-ish string (e.g. '2547XXXXXXXX'),
    or None if not configured. Used by all public WhatsApp-link routes.
    """
    from app.models import Setting
    from flask import current_app

    setting = Setting.query.filter_by(
        key="company_phone",
        is_published=True,
    ).first()

    raw = (
        setting.value_text
        if setting and setting.value_text
        else current_app.config.get("WHATSAPP_BUSINESS_NUMBER", "")
    )
    phone = re.sub(r"\D", "", raw or "")
    return phone or None






def _dump_rental_item(i, *, whatsapp_phone: str | None, category=None) -> dict:
    """
    Public shape for an InventoryItem.
    Deliberately omits quantity_owned (internal stock).
    Includes a ready-to-use wa_link so the frontend stays phone-agnostic.
    """
    cat = category or i.category
    wa_link = None
    if whatsapp_phone:
        wa_link = wa_link_for_rental_item(
            item_name=i.name,
            phone=whatsapp_phone,
            category_name=cat.name if cat else None,
            source_ref=f"rental:{i.slug}",
        )

    return {
        "id": str(i.id),
        "slug": i.slug,
        "name": i.name,
        "short_description": i.short_description,
        "featured_image_url": i.featured_image_url,
        "gallery": i.gallery or [],
        "tags": i.tags or [],
        "from_price": float(i.unit_price_hint) if i.unit_price_hint is not None else None,
        "unit": i.unit,
        "currency": i.currency,
        "availability_note": i.quantity_available_note,   # public trust signal, NOT stock count
        "category": (
            {"slug": cat.slug, "name": cat.name} if cat else None
        ),
        "wa_link": wa_link,
    }
