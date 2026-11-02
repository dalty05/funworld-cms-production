# api.py

from flask import Blueprint, g, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError




from app import db
from app.audit import write_audit
from app.errors import ok, error, NotFoundError
from app.models import ( Permission, Role, User, )
from app.schemas import ( LoginSchema, PermissionSchema, RoleCreateSchema, RoleSchema, UserCreateSchema, UserSchema, TimelineEventSchema, )
from app.security import ( PasswordPolicyError, idempotent, issue_tokens, login_required, require_permission, revoke_token, validate_password_strength,
)
from app.extensions import limiter
from app.services import ( authenticate, create_role, delete_role, get_role, list_roles, update_role,  )
from datetime import datetime, timezone, timedelta

from app.realtime import emit_alert, ROOM_ADMINS, ROOM_SALES, ROOM_OPS, ROOM_ALL




from app.errors import ForbiddenError


from app.models import utcnow 
from flask import has_request_context
from app.services import record_event

from app.models import TimelineEvent,RoleAssignment

from app.services import wa_link_for_rental_item

from app.services import get_public_whatsapp_phone
from app.images import process_and_store_image





api_v1 = Blueprint("api_v1", __name__)


# ─────────────────────────────────────────────────────────────
# Schema instances
# ─────────────────────────────────────────────────────────────

login_schema = LoginSchema()
user_schema = UserSchema()
user_create_schema = UserCreateSchema()
role_schema = RoleSchema()
role_create_schema = RoleCreateSchema()
permission_schema = PermissionSchema(many=True)

timeline_schema = TimelineEventSchema(many=True)







# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _validation_error(exc: ValidationError):
    """Standard 422 response for marshmallow validation failures."""
    return error(
        "validation_error",
        "Invalid request body.",
        details=exc.messages,
        status=422,
    )


def _dump_user_brief(user: User | None) -> dict | None:
    if user is None:
        return None
    return {"id": str(user.id), "full_name": user.full_name, "email": user.email}





# ─── Health ────────────────────────────────────────────────────

@api_v1.get("/ping")
def ping():
    return ok({"pong": True})


# ─── Auth ──────────────────────────────────────────────────────

@api_v1.post("/auth/login")
@limiter.limit("10 per minute; 50 per hour")
# NOTE: @idempotent removed — login is not a resource-creation endpoint.
def login():
    try:
        data = login_schema.load(request.get_json() or {})
    except ValidationError as exc:
        return _validation_error(exc)

    try:
        result = authenticate(data["email"], data["password"])
    except Exception:
        import logging
        logging.getLogger(__name__).exception("authenticate_failed")
        return error("unauthorized", "Invalid email or password.", status=401)

    if not result or not result.get("user"):
        return error("unauthorized", "Invalid email or password.", status=401)

    user = result["user"]

    write_audit("auth.login", entity_type="user", entity_id=str(user.id))
    db.session.commit()

    return ok({
        "user": user_schema.dump(user),
        "tokens": result["tokens"],
    })


@api_v1.post("/auth/logout")
@jwt_required()
def logout():
    claims = get_jwt()
    user = db.session.get(User, get_jwt_identity())
    if user:
        revoke_token(claims)
        user.token_version = (user.token_version or 0) + 1
        write_audit(
            "auth.logout", entity_type="user", entity_id=str(user.id),
            after={"token_version": user.token_version},
        )
    db.session.commit()
    return ok()


@api_v1.post("/auth/refresh")
@limiter.limit("30 per minute")
@jwt_required(refresh=True)
def refresh_auth_tokens():
    claims = get_jwt()
    user = db.session.get(User, get_jwt_identity())
    if not user or not user.is_active:
        return error("unauthorized", "Authentication required.", status=401)
    if int(claims.get("tv", 0)) != int(user.token_version or 0):
        return error("token_revoked", "This refresh token has been revoked.", status=401)

    revoke_token(claims)
    try:
        db.session.flush()
    except IntegrityError:
        db.session.rollback()
        return error("token_replayed", "This refresh token has already been used.", status=401)

    tokens = issue_tokens(user.id)
    db.session.commit()
    return ok({"tokens": tokens})


# ─── Roles ─────────────────────────────────────────────────────

@api_v1.get("/roles")
@require_permission("role.view")
def get_roles():
    return ok(role_schema.dump(list_roles(), many=True))


@api_v1.post("/roles")
@require_permission("role.create")
@idempotent
def post_role():
    try:
        data = role_create_schema.load(request.get_json() or {})
    except ValidationError as exc:
        return _validation_error(exc)

    role = create_role(data)

    write_audit(
        "role.created",
        entity_type="role",
        entity_id=str(role.id),
        after=data,
    )
    db.session.commit()

    emit_alert("role.created", {"id": str(role.id), "slug": role.slug}, room=ROOM_ADMINS)
    return ok(role_schema.dump(role), status=201)


@api_v1.patch("/roles/<uuid:role_id>")
@require_permission("role.edit")
@idempotent
def patch_role(role_id):
    role = get_role(role_id)
    before = role_schema.dump(role)

    try:
        data = role_create_schema.load(request.get_json() or {}, partial=True)
    except ValidationError as exc:
        return _validation_error(exc)

    update_role(role, data, actor=g.current_user)
    after = role_schema.dump(role)

    write_audit(
        "role.updated",
        entity_type="role",
        entity_id=str(role.id),
        before=before,
        after=after,
    )
    db.session.commit()

    emit_alert("role.updated", {"id": str(role.id)}, room=ROOM_ADMINS)
    return ok(after)


@api_v1.delete("/roles/<uuid:role_id>")
@require_permission("role.delete")
@idempotent
def delete_role_route(role_id):
    role = get_role(role_id)
    before = role_schema.dump(role)

    delete_role(role, actor=g.current_user)

    write_audit(
        "role.deleted",
        entity_type="role",
        entity_id=str(role_id),
        before=before,
    )
    db.session.commit()

    emit_alert("role.deleted", {"id": str(role_id)}, room=ROOM_ADMINS)
    return ok()








#phase 8 - TIMELINE & AUDIT

from app.models import TimelineEvent, AuditLog
from app.security import require_permission


# ─── Timeline reader ────────────────────────────────────────────────

@api_v1.get("/timeline")
@login_required
@require_permission("audit.view")
def read_timeline():
    """
    Query timeline events.
    Filters: entity_type, entity_id, event_type, actor_user_id,
             since, until, limit.
    """
    q = TimelineEvent.query

    if et := request.args.get("entity_type"):
        q = q.filter(TimelineEvent.entity_type == et)
    if eid := request.args.get("entity_id"):
        q = q.filter(TimelineEvent.entity_id == eid)
    if evt := request.args.get("event_type"):
        q = q.filter(TimelineEvent.event_type == evt)
    if actor := request.args.get("actor_user_id"):
        q = q.filter(TimelineEvent.actor_user_id == actor)

    since = request.args.get("since")
    if since:
        q = q.filter(TimelineEvent.created_at >= since)
    until = request.args.get("until")
    if until:
        q = q.filter(TimelineEvent.created_at <= until)

    limit = min(int(request.args.get("limit", 100)), 500)
    rows = q.order_by(TimelineEvent.created_at.desc()).limit(limit).all()

    return ok([
        {
            "id": str(r.id),
            "entity_type": r.entity_type,
            "entity_id": str(r.entity_id),
            "event_type": r.event_type,
            "actor_type": r.actor_type,
            "actor_user_id": str(r.actor_user_id) if r.actor_user_id else None,
            "summary": r.summary,
            "metadata": r.metadata_json,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ])


# ─── Audit reader ───────────────────────────────────────────────────

@api_v1.get("/audit-logs")
@login_required
@require_permission("audit.view")
def read_audit_logs():
    """
    Query audit rows.
    Filters: action, entity_type, entity_id, actor_user_id,
             since, until, limit.
    """
    q = AuditLog.query

    if action := request.args.get("action"):
        q = q.filter(AuditLog.action == action)
    if et := request.args.get("entity_type"):
        q = q.filter(AuditLog.entity_type == et)
    if eid := request.args.get("entity_id"):
        q = q.filter(AuditLog.entity_id == str(eid))
    if actor := request.args.get("actor_user_id"):
        q = q.filter(AuditLog.actor_user_id == actor)

    since = request.args.get("since")
    if since:
        q = q.filter(AuditLog.created_at >= since)
    until = request.args.get("until")
    if until:
        q = q.filter(AuditLog.created_at <= until)

    limit = min(int(request.args.get("limit", 100)), 500)
    rows = q.order_by(AuditLog.created_at.desc()).limit(limit).all()

    return ok([
        {
            "id": str(r.id),
            "actor_user_id": str(r.actor_user_id) if r.actor_user_id else None,
            "actor_type": r.actor_type,
            "action": r.action,
            "entity_type": r.entity_type,
            "entity_id": r.entity_id,
            "before": r.before,
            "after": r.after,
            "row_hash": r.row_hash,
            "request_id": r.request_id,
            "ip_address": r.ip_address,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ])


# ─── Audit chain verification ───────────────────────────────────────

@api_v1.get("/audit-logs/verify")
@login_required
@require_permission("audit.view")
def verify_audit():
    """Verify the audit chain integrity end to end. O(n)."""
    from app.audit import verify_audit_chain
    limit = request.args.get("limit")
    result = verify_audit_chain(limit=int(limit) if limit else None)
    return ok(result)



from app.models import ContactMessage 
from app.services import normalize_phone 

@api_v1.post("/contact-messages")
@limiter.limit("300 per hour")
@idempotent
def post_contact_message():
    body = request.get_json() or {}
    required = ["full_name", "message"]
    missing = [f for f in required if not body.get(f)]
    if missing:
        return error("validation_error",
                     f"Missing: {', '.join(missing)}",
                     details={"fields": missing}, status=422)

    if not body.get("email") and not body.get("phone"):
        return error("validation_error",
                     "Either email or phone is required.",
                     details={"fields": ["email", "phone"]}, status=422)

    msg = ContactMessage(
        full_name=body["full_name"].strip(),
        email=(body.get("email") or "").strip() or None,
        phone=normalize_phone(body.get("phone")),
        subject=(body.get("subject") or "").strip()[:255] or None,
        message=body["message"],
    )
    db.session.add(msg)
    db.session.flush()

    write_audit("contact_message.created",
                entity_type="contact_message", entity_id=str(msg.id))

    db.session.commit()
    emit_alert("contact.message.received",)
    return ok({"id": str(msg.id)}, status=201)


import re

from flask import current_app, request

from app.models import Setting

from app.services import ( build_wa_link, wa_link_for_package, wa_link_for_service, )

@api_v1.get("/whatsapp/link")
@limiter.limit("60 per hour")
def whatsapp_link():
    """
    Public endpoint. Returns a wa.me deep link with a prefilled message.
    The company_phone setting supplies the WhatsApp destination number.
    """
    kind = (request.args.get("kind") or "custom").lower()
    ref = request.args.get("ref")

    setting = Setting.query.filter_by(
        key="company_phone",
        is_published=True,
    ).first()

    # Temporary fallback for environments where the setting is not seeded.
    raw_phone = (
        setting.value_text
        if setting and setting.value_text
        else current_app.config.get("WHATSAPP_BUSINESS_NUMBER", "")
    )

    phone = get_public_whatsapp_phone()

    if not phone:
        return error(
            "whatsapp_not_configured",
            "WhatsApp contact number has not been configured.",
            503,
        )

    if kind == "package":
        name = request.args.get("name") or "package"
        link = wa_link_for_package(name, phone, source_ref=ref)

    elif kind == "service":
        name = request.args.get("name") or "service"
        link = wa_link_for_service(name, phone, source_ref=ref)

    else:
        message = request.args.get("text") or "Hello Funworld Events!"
        link = build_wa_link(
            phone=phone,
            message=message,
            source_ref=ref,
        )

    return ok({"link": link})


#──────── Phase 12: Blog ─────────────────────────────────────────────────────

from app.models import (
    BlogPost, BlogPostStatus, BlogCategory, BlogTag,
)
from app.services import (
    list_published_posts, get_published_post, increment_post_views,
    suggest_internal_links,
)


# ─── Public list ────────────────────────────────────────────────────

@api_v1.get("/blog")
def public_list_blog():
    """
    Public blog index. Supports:
      ?category=<slug>
      ?tag=<slug>
      ?author=<uuid>
      ?featured=true
      ?limit=20&offset=0
    """
    category = request.args.get("category")
    tag = request.args.get("tag")
    author = request.args.get("author")
    featured = request.args.get("featured") == "true"
    limit = min(int(request.args.get("limit", 20)), 100)
    offset = int(request.args.get("offset", 0))

    posts, total = list_published_posts(
        category_slug=category,
        tag_slug=tag,
        author_id=author,
        limit=limit,
        offset=offset,
        featured_only=featured,
    )

    return ok(
        [_dump_blog_post_brief(p) for p in posts],
        meta={
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(posts) < total,
        },
    )


# ─── Public detail ──────────────────────────────────────────────────

@api_v1.get("/blog/<slug>")
def public_get_blog(slug):
    post = get_published_post(slug)
    if not post:
        raise NotFoundError("Post not found.")

    increment_post_views(post)
    db.session.commit()

    return ok(_dump_blog_post_full(post))


# ─── Categories & tags (public) ────────────────────────────────────

@api_v1.get("/blog/categories")
def public_list_blog_categories():
    cats = BlogCategory.query.order_by(BlogCategory.sort_order.asc()).all()
    return ok([
        {
            "slug": c.slug,
            "name": c.name,
            "description": c.description,
            "seo_title": c.seo_title,
            "seo_description": c.seo_description,
        }
        for c in cats
    ])


@api_v1.get("/blog/tags")
def public_list_blog_tags():
    tags = BlogTag.query.order_by(BlogTag.name.asc()).all()
    return ok([{"slug": t.slug, "name": t.name} for t in tags])


# ─── Serializers ────────────────────────────────────────────────────

def _dump_blog_post_brief(p: BlogPost) -> dict:
    return {
        "slug": p.slug,
        "title": p.title,
        "excerpt": p.excerpt,
        "featured_image": p.featured_image_url,
        "featured_image_alt": p.featured_image_alt,
        "published_at": p.published_at.isoformat() if p.published_at else None,
        "reading_minutes": p.reading_minutes,
        "featured": p.featured,
        "author": (
            {"id": str(p.author.id), "full_name": p.author.full_name}
            if p.author else None
        ),
        "categories": [{"slug": c.slug, "name": c.name} for c in p.categories],
        "tags": [{"slug": t.slug, "name": t.name} for t in p.tags],
    }

def _dump_blog_post_full(p: BlogPost) -> dict:
    return {
        **_dump_blog_post_brief(p),
        "body_html": p.body_html,
        "seo_title": p.seo_title or p.title,
        "seo_description": p.seo_description or p.excerpt,
        "canonical_url": p.canonical_url,
        "og_image_url": p.og_image_url or p.featured_image_url,
        "view_count": p.view_count,
        "updated_at": p.updated_at.isoformat(),
        "related": _get_related_blog_posts(p),
    }

def _get_related_blog_posts(post: BlogPost, limit: int = 3) -> list[dict]:
    category_ids = [category.id for category in post.categories]

    query = BlogPost.query.filter(
        BlogPost.id != post.id,
        BlogPost.status == BlogPostStatus.PUBLISHED,
    )

    if category_ids:
        # Prioritize posts sharing categories with the current article.
        related_posts = (
            query
            .filter(BlogPost.categories.any(BlogCategory.id.in_(category_ids)))
            .order_by(BlogPost.published_at.desc())
            .limit(limit)
            .all()
        )
    else:
        related_posts = []

    # Fill remaining slots with other recently published posts.
    if len(related_posts) < limit:
        existing_ids = [post.id for post in related_posts]
        existing_ids.append(post.id)

        remaining = (
            BlogPost.query
            .filter(
                BlogPost.id.notin_(existing_ids),
                BlogPost.status == BlogPostStatus.PUBLISHED,
            )
            .order_by(BlogPost.published_at.desc())
            .limit(limit - len(related_posts))
            .all()
        )

        related_posts.extend(remaining)

    return [_dump_blog_post_brief(p) for p in related_posts]


from app.services import (
    create_blog_post, update_blog_post,
    submit_post_for_review, approve_post, reject_post,
    publish_post, archive_post, publish_due_scheduled_posts,
    generate_unique_slug,
)
from app.schemas import (
    blog_post_create_schema, blog_post_update_schema,
    blog_post_schedule_schema, blog_post_reject_schema,
    blog_category_schema, blog_categories_schema,
    blog_tag_schema, blog_tags_schema,
)

from app.models import BlogPostRevision


# ─── Admin: list posts (all statuses) ───────────────────────────────

@api_v1.get("/admin/blog/posts")
@login_required
@require_permission("content.view")
def admin_list_blog_posts():
    q = BlogPost.query
    if s := request.args.get("status"):
        try:
            q = q.filter(BlogPost.status == BlogPostStatus(s))
        except ValueError:
            return error("validation_error", "Invalid status.",
                         details={"allowed": [x.value for x in BlogPostStatus]},
                         status=422)
    if a := request.args.get("author"):
        q = q.filter(BlogPost.author_user_id == a)

    limit = min(int(request.args.get("limit", 50)), 200)
    posts = q.order_by(BlogPost.updated_at.desc()).limit(limit).all()

    return ok([{
        **_dump_blog_post_brief(p),
        "id": str(p.id),
        "status": p.status.value,
        "scheduled_for": p.scheduled_for.isoformat() if p.scheduled_for else None,
        "updated_at": p.updated_at.isoformat(),
    } for p in posts])


# ─── Admin: detail (any status) ────────────────────────────────────

@api_v1.get("/admin/blog/posts/<uuid:post_id>")
@login_required
@require_permission("content.view")
def admin_get_blog_post(post_id):
    post = BlogPost.query.get(post_id)
    if not post:
        raise NotFoundError("Post not found.")

    revisions = (
        BlogPostRevision.query
        .filter_by(post_id=post.id)
        .order_by(BlogPostRevision.revision_number.desc())
        .limit(20)
        .all()
    )

    return ok({
        "id": str(post.id),
        "slug": post.slug,
        "title": post.title,
        "excerpt": post.excerpt,
        "body_markdown": post.body_markdown,
        "body_html": post.body_html,
        "featured_image_url": post.featured_image_url,
        "featured_image_alt": post.featured_image_alt,
        "status": post.status.value,
        "featured": post.featured,
        "reading_minutes": post.reading_minutes,
        "view_count": post.view_count,
        "seo_title": post.seo_title,
        "seo_description": post.seo_description,
        "canonical_url": post.canonical_url,
        "og_image_url": post.og_image_url,
        "published_at": post.published_at.isoformat() if post.published_at else None,
        "scheduled_for": post.scheduled_for.isoformat() if post.scheduled_for else None,
        "archived_at": post.archived_at.isoformat() if post.archived_at else None,
        "rejection_reason": post.rejection_reason,
        "author": (
            {"id": str(post.author.id), "full_name": post.author.full_name}
            if post.author else None
        ),
        "reviewed_by": (
            {"id": str(post.reviewed_by.id), "full_name": post.reviewed_by.full_name}
            if post.reviewed_by else None
        ),
        "categories": [{"id": str(c.id), "slug": c.slug, "name": c.name}
                       for c in post.categories],
        "tags": [{"id": str(t.id), "slug": t.slug, "name": t.name}
                 for t in post.tags],
        "revisions": [
            {
                "id": str(r.id),
                "revision_number": r.revision_number,
                "title": r.title,
                "saved_by_user_id": str(r.saved_by_user_id) if r.saved_by_user_id else None,
                "created_at": r.created_at.isoformat(),
            }
            for r in revisions
        ],
        "created_at": post.created_at.isoformat(),
        "updated_at": post.updated_at.isoformat(),
    })


# ─── Admin: create ──────────────────────────────────────────────────

@api_v1.post("/admin/blog/posts")
@login_required
@require_permission("content.create")
@idempotent
def admin_create_blog_post():
    try:
        data = blog_post_create_schema.load(request.get_json() or {})
    except ValidationError as exc:
        return _validation_error(exc)

    post = create_blog_post(
        title=data["title"],
        body_markdown=data.get("body_markdown", ""),
        excerpt=data.get("excerpt"),
        featured_image_url=data.get("featured_image_url"),
        featured_image_alt=data.get("featured_image_alt"),
        seo_title=data.get("seo_title"),
        seo_description=data.get("seo_description"),
        canonical_url=data.get("canonical_url"),
        og_image_url=data.get("og_image_url"),
        featured=data.get("featured", False),
        author_user_id=g.current_user.id,
        category_slugs=data.get("category_slugs", []),
        tag_slugs=data.get("tag_slugs", []),
    )
    write_audit("blog_post.created", entity_type="blog_post",
                entity_id=str(post.id),
                after={"slug": post.slug, "title": post.title})
    db.session.commit()

    return ok({"id": str(post.id), "slug": post.slug, "status": post.status.value},
              status=201)


# ─── Admin: update ──────────────────────────────────────────────────

@api_v1.patch("/admin/blog/posts/<uuid:post_id>")
@login_required
@require_permission("content.edit")
def admin_update_blog_post(post_id):
    post = BlogPost.query.get(post_id)
    if not post:
        raise NotFoundError("Post not found.")
    if post.status == BlogPostStatus.ARCHIVED:
        return error("invalid_state", "Archived posts cannot be edited.", status=409)

    try:
        data = blog_post_update_schema.load(request.get_json() or {}, partial=True)
    except ValidationError as exc:
        return _validation_error(exc)

    update_blog_post(post, data=data, author_user_id=g.current_user.id)
    write_audit("blog_post.updated", entity_type="blog_post",
                entity_id=str(post.id),
                after={"title": post.title})
    db.session.commit()
    return ok({"id": str(post.id), "updated_at": post.updated_at.isoformat()})


# image processing

def _upload_blog_image():
    if "file" not in request.files:
        return error(
            "validation_error",
            "No file provided.",
            details={"field": "file"},
            status=422,
        )

    f = request.files["file"]

    if not f.filename:
        return error(
            "validation_error",
            "Empty filename.",
            details={"field": "file"},
            status=422,
        )

    try:
        image = process_and_store_image(
            file_bytes=f.read(),
            mime_type=f.mimetype or "image/jpeg",
            prefix="blog",
        )
    except ValueError as exc:
        return error("validation_error", str(exc), status=422)

    return ok({
        "url": image["url"],
        "thumb_url": image["thumb_url"],
        "width": image["width"],
        "height": image["height"],
        "size_bytes": image["size_bytes"],
    }, status=201)


@api_v1.post("/admin/blog/upload-image")
@login_required
@require_permission("content.create")
def admin_upload_blog_image_create():
    return _upload_blog_image()


@api_v1.post("/admin/blog/upload-image/edit")
@login_required
@require_permission("content.edit")
def admin_upload_blog_image_edit():
    return _upload_blog_image()





# ─── Admin: workflow ────────────────────────────────────────────────

@api_v1.post("/admin/blog/posts/<uuid:post_id>/submit")
@login_required
@require_permission("content.edit")
def admin_submit_post(post_id):
    post = BlogPost.query.get(post_id)
    if not post:
        raise NotFoundError("Post not found.")
    try:
        submit_post_for_review(post, actor_user_id=g.current_user.id)
    except ValueError as exc:
        return error("invalid_state", str(exc), status=409)
    write_audit("blog_post.submitted", entity_type="blog_post", entity_id=str(post.id))
    db.session.commit()
    return ok({"status": post.status.value})


@api_v1.post("/admin/blog/posts/<uuid:post_id>/approve")
@login_required
@require_permission("content.publish")
def admin_approve_post(post_id):
    post = BlogPost.query.get(post_id)
    if not post:
        raise NotFoundError("Post not found.")
    try:
        approve_post(post, actor_user_id=g.current_user.id)
    except ValueError as exc:
        return error("invalid_state", str(exc), status=409)
    write_audit("blog_post.approved", entity_type="blog_post", entity_id=str(post.id))
  
    db.session.commit()
    return ok({"status": post.status.value})


@api_v1.post("/admin/blog/posts/<uuid:post_id>/reject")
@login_required
@require_permission("content.publish")
def admin_reject_post(post_id):
    post = BlogPost.query.get(post_id)
    if not post:
        raise NotFoundError("Post not found.")
    try:
        data = blog_post_reject_schema.load(request.get_json() or {})
    except ValidationError as exc:
        return _validation_error(exc)
    try:
        reject_post(post, reason=data["reason"], actor_user_id=g.current_user.id)
    except ValueError as exc:
        return error("invalid_state", str(exc), status=409)
    write_audit("blog_post.rejected", entity_type="blog_post", entity_id=str(post.id),
                after={"reason": data["reason"]})

    
    
    
    db.session.commit()
    return ok({"status": post.status.value})


@api_v1.post("/admin/blog/posts/<uuid:post_id>/schedule")
@login_required
@require_permission("content.publish")
def admin_schedule_post(post_id):
    post = BlogPost.query.get(post_id)
    if not post:
        raise NotFoundError("Post not found.")
    try:
        data = blog_post_schedule_schema.load(request.get_json() or {})
    except ValidationError as exc:
        return _validation_error(exc)

    if post.status not in (BlogPostStatus.SCHEDULED, BlogPostStatus.REVIEW):
        return error("invalid_state", "Post must be in review or scheduled.", status=409)

    post.status = BlogPostStatus.SCHEDULED
    post.scheduled_for = data["scheduled_for"]
    write_audit("blog_post.scheduled", entity_type="blog_post", entity_id=str(post.id),
                after={"scheduled_for": data["scheduled_for"].isoformat()})
    db.session.commit()
    return ok({"status": post.status.value,
               "scheduled_for": post.scheduled_for.isoformat()})


@api_v1.post("/admin/blog/posts/<uuid:post_id>/publish")
@login_required
@require_permission("content.publish")
def admin_publish_post(post_id):
    post = BlogPost.query.get(post_id)
    if not post:
        raise NotFoundError("Post not found.")
    try:
        publish_post(post, actor_user_id=g.current_user.id)
    except ValueError as exc:
        return error("invalid_state", str(exc), status=409)
    write_audit("blog_post.published", entity_type="blog_post", entity_id=str(post.id))
    db.session.commit()
    emit_alert("blog_post.published",
               {"id": str(post.id), "slug": post.slug, "title": post.title},
               room=ROOM_SALES)
    return ok({"status": post.status.value,
               "published_at": post.published_at.isoformat()})


@api_v1.post("/admin/blog/posts/<uuid:post_id>/archive")
@login_required
@require_permission("content.publish")
def admin_archive_post(post_id):
    post = BlogPost.query.get(post_id)
    if not post:
        raise NotFoundError("Post not found.")
    archive_post(post, actor_user_id=g.current_user.id)
    write_audit("blog_post.archived", entity_type="blog_post", entity_id=str(post.id))
    db.session.commit()
    return ok({"status": post.status.value})


@api_v1.post("/admin/blog/publish-due")
@login_required
@require_permission("content.publish")
def admin_publish_due():
    n = publish_due_scheduled_posts()
    return ok({"published": n})


# ─── Admin: internal link suggestions ───────────────────────────────

@api_v1.post("/admin/blog/suggest-links")
@login_required
@require_permission("content.edit")
def admin_suggest_links():
    body = request.get_json() or {}
    text = (body.get("text") or "").strip()
    if not text:
        return ok([])
    return ok(suggest_internal_links(text))


# ─── Admin: categories CRUD ────────────────────────────────────────

@api_v1.get("/admin/blog/categories")
@login_required
@require_permission("content.view")
def admin_list_categories():
    cats = BlogCategory.query.order_by(BlogCategory.sort_order.asc()).all()
    return ok([{
        "id": str(c.id), "slug": c.slug, "name": c.name,
        "description": c.description,
        "seo_title": c.seo_title, "seo_description": c.seo_description,
        "sort_order": c.sort_order,
    } for c in cats])


@api_v1.post("/admin/blog/categories")
@login_required
@require_permission("content.create")
def admin_create_category():
    try:
        data = blog_category_schema.load(request.get_json() or {})
    except ValidationError as exc:
        return _validation_error(exc)

    if BlogCategory.query.filter_by(slug=data["slug"]).first():
        return error("conflict", "Category slug already exists.", status=409)

    cat = BlogCategory(**data)
    db.session.add(cat)
    write_audit("blog_category.created", entity_type="blog_category",
                entity_id=str(cat.id), after={"slug": cat.slug})
    db.session.commit()
    return ok({"id": str(cat.id), "slug": cat.slug}, status=201)


# ─── Admin: tags CRUD ──────────────────────────────────────────────

@api_v1.get("/admin/blog/tags")
@login_required
@require_permission("content.view")
def admin_list_tags():
    tags = BlogTag.query.order_by(BlogTag.name.asc()).all()
    return ok([{"id": str(t.id), "slug": t.slug, "name": t.name} for t in tags])


@api_v1.post("/admin/blog/tags")
@login_required
@require_permission("content.create")
def admin_create_tag():
    try:
        data = blog_tag_schema.load(request.get_json() or {})
    except ValidationError as exc:
        return _validation_error(exc)

    if BlogTag.query.filter_by(slug=data["slug"]).first():
        return error("conflict", "Tag slug already exists.", status=409)

    tag = BlogTag(**data)
    db.session.add(tag)
    write_audit("blog_tag.created", entity_type="blog_tag",
                entity_id=str(tag.id), after={"slug": tag.slug})
    db.session.commit()
    return ok({"id": str(tag.id), "slug": tag.slug}, status=201)



@api_v1.get("/admin/reports/blog-performance")
@login_required
@require_permission("enquiry.view.all")
def report_blog_performance():
    """
    For each published post: views + enquiries attributed to it.
    Joins blog_posts against enquiries.source_page = '/blog/<slug>'.
    """
    posts = BlogPost.query.filter(BlogPost.status == BlogPostStatus.PUBLISHED).all()
    results = []
    for p in posts:
        path = f"/blog/{p.slug}"
        results.append({
            "slug": p.slug,
            "title": p.title,
            "views": p.view_count,
           
            "conversion_rate": round(count / p.view_count, 4) if p.view_count else 0,
            "published_at": p.published_at.isoformat() if p.published_at else None,
        })
    return 


@api_v1.get("/auth/me")
@login_required
def get_me():
    user = g.current_user
    permissions = set()
    for assignment in user.role_assignments:
        if not assignment.is_active:
            continue
        for p in assignment.role.permissions:
            permissions.add(p.code)
    return ok({
        "id": str(user.id),
        "full_name": user.full_name,
        "email": user.email,
        "roles": [a.role.slug for a in user.role_assignments if a.is_active],
        "permissions": sorted(permissions),
    })



# ─── Permissions ───────────────────────────────────────────────


@api_v1.get("/permissions")
@login_required
@require_permission("role.view")
def list_permissions():
    perms = Permission.query.order_by(Permission.code.asc()).all()
    return ok([{"id": str(p.id), "code": p.code, "category": p.category, "description": p.description} for p in perms])



# @api_v1.get("/users")
# @login_required
# @require_permission("user.view")
# def list_users_api():
#     users = User.query.order_by(User.created_at.desc()).all()
#     return ok([{
#         "id": str(u.id),
#         "full_name": u.full_name,
#         "email": u.email,
#         "is_active": u.is_active,
#         "roles": [a.role.slug for a in u.role_assignments if a.is_active],
#     } for u in users])



# ─── Users list ─────────────────────────────────────────────────────

@api_v1.get("/users")
@login_required
@require_permission("user.view")
def list_users_endpoint():
    users = User.query.order_by(User.created_at.desc()).all()
    return ok([{
        "id": str(u.id),
        "full_name": u.full_name,
        "email": u.email,
        "phone": u.phone,
        "is_active": u.is_active,
        "roles": [
            {
                "id": str(a.id),
                "slug": a.role.slug,
                "name": a.role.name,
                "scope_type": a.scope_type,
            }
            for a in u.role_assignments if a.is_active
        ],
    } for u in users])



@api_v1.get("/users/<uuid:user_id>")
@login_required
@require_permission("user.view")
def get_user_endpoint(user_id):
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError("User not found.")
    return ok({
        "id": str(user.id),
        "full_name": user.full_name,
        "email": user.email,
        "phone": user.phone,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        "token_version": user.token_version,
        "roles": [
            {
                "id": str(a.id),
                "slug": a.role.slug,
                "name": a.role.name,
                "scope_type": a.scope_type,
                "scope_id": str(a.scope_id) if a.scope_id else None,
            }
            for a in user.role_assignments if a.is_active
        ],
    })


@api_v1.post("/users/<uuid:user_id>/revoke-tokens")
@login_required
@require_permission("user.deactivate")
@idempotent
def post_revoke_user_tokens(user_id):
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError("User not found.")

    user.token_version = (user.token_version or 0) + 1
    write_audit(
        "user.tokens_revoked",
        entity_type="user",
        entity_id=str(user.id),
        after={"token_version": user.token_version},
    )
    db.session.commit()
    return ok({"id": str(user.id), "token_version": user.token_version})



from app.security import hash_password


# ─── Users: create ──────────────────────────────────────────────────

@api_v1.post("/users")
@login_required
@require_permission("user.invite")
@idempotent
def post_user():
    body = request.get_json() or {}
    required = ["full_name", "email", "password"]
    missing = [f for f in required if not body.get(f)]
    if missing:
        return error("validation_error",
                     f"Missing: {', '.join(missing)}",
                     details={"fields": missing}, status=422)

    try:
        validate_password_strength(body["password"])
    except PasswordPolicyError as exc:
        return error(
            "weak_password", str(exc), details={"field": "password"}, status=422,
        )

    email = body["email"].strip().lower()
    if User.query.filter(db.func.lower(User.email) == email).first():
        return error("conflict", "A user with that email already exists.", status=409)

    user = User(
        email=email,
        full_name=body["full_name"].strip(),
        phone=normalize_phone(body.get("phone")),
        password_hash=hash_password(body["password"]),
        is_active=bool(body.get("is_active", True)),
        is_verified=False,
    )
    db.session.add(user)
    db.session.flush()

    # Optional: assign initial roles
    role_slugs = body.get("role_slugs") or []
    if role_slugs:
        for slug in role_slugs:
            role = Role.query.filter_by(slug=slug).first()
            if not role:
                continue
            db.session.add(RoleAssignment(
                user_id=user.id,
                role_id=role.id,
                scope_type="global",
                is_active=True,
                granted_by_user_id=g.current_user.id,
                granted_at=utcnow(),
            ))

    write_audit("user.created", entity_type="user", entity_id=str(user.id),
                after={"email": user.email, "roles": role_slugs})
    db.session.commit()

    return ok({
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
    }, status=201)


# ─── Users: assign / revoke role ────────────────────────────────────

@api_v1.post("/users/<uuid:user_id>/roles")
@login_required
@require_permission("role.assign")
@idempotent
def post_assign_user_role(user_id):
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError("User not found.")

    body = request.get_json() or {}
    slug = body.get("role_slug")
    scope_type = body.get("scope_type", "global")
    scope_id = body.get("scope_id")

    if not slug:
        return error("validation_error", "role_slug is required.",
                     details={"fields": ["role_slug"]}, status=422)

    role = Role.query.filter_by(slug=slug).first()
    if not role:
        return error("validation_error", "Role not found.",
                     details={"role_slug": slug}, status=422)

    # Self-grant guardrail
    from app.security import can_assign_role
    if not can_assign_role(g.current_user, role):
        return error("forbidden",
                     "You cannot assign a role with permissions you don't hold.",
                     status=403)

    # Idempotent: skip if already assigned
    existing = RoleAssignment.query.filter_by(
        user_id=user.id, role_id=role.id,
        scope_type=scope_type, scope_id=scope_id,
    ).first()
    if existing:
        return ok({"id": str(existing.id), "noop": True})

    assignment = RoleAssignment(
        user_id=user.id,
        role_id=role.id,
        scope_type=scope_type,
        scope_id=scope_id,
        is_active=True,
        granted_by_user_id=g.current_user.id,
        granted_at=utcnow(),
    )
    db.session.add(assignment)

    write_audit("role.assigned", entity_type="user", entity_id=str(user.id),
                after={"role": role.slug, "scope_type": scope_type})
    db.session.commit()

    return ok({"id": str(assignment.id), "role": role.slug}, status=201)


@api_v1.delete("/users/<uuid:user_id>/roles/<uuid:assignment_id>")
@login_required
@require_permission("role.assign")
def delete_user_role(user_id, assignment_id):
    assignment = RoleAssignment.query.get(assignment_id)
    if not assignment or assignment.user_id != user_id:
        raise NotFoundError("Role assignment not found.")
    assignment.is_active = False
    write_audit("role.revoked", entity_type="user", entity_id=str(user_id),
                after={"role": assignment.role.slug})
    db.session.commit()
    return ok({"id": str(assignment.id), "is_active": False})



# public services endpoints




from app.models import ServiceCategory, Service, Package, PackageStatus
from app.services import (
    list_published_services, get_published_service,
    list_published_packages, get_published_package,
)


# ─── Public: Service catalogue ───────────────────────────────────────
from sqlalchemy.orm import selectinload


@api_v1.get("/services/categories")
def public_list_service_categories():
    cats = (
        ServiceCategory.query
        .options(selectinload(ServiceCategory.services))
        .order_by(ServiceCategory.sort_order.asc())
        .all()
    )

    return ok([{
        "slug": c.slug,
        "name": c.name,
        "short_description": c.short_description,

        # Category image first, then first published service image.
        "hero_image_url": get_category_image(c),

        "accent_color": c.accent_color,
        "service_count": sum(
            1 for s in c.services if s.is_published
        ),
    } for c in cats])









@api_v1.get("/services/categories/<slug>")
def public_get_service_category(slug):
    cat = ServiceCategory.query.filter_by(slug=slug).first()
    if not cat:
        raise NotFoundError("Category not found.")
    services = [s for s in cat.services if s.is_published]
    return ok({
        "slug": cat.slug,
        "name": cat.name,
        "short_description": cat.short_description,
        "long_description": cat.long_description,
        "hero_image_url": get_category_image(cat),
        "seo_title": cat.seo_title,
        "seo_description": cat.seo_description,
        "services": [{
            "slug": s.slug,
            "name": s.name,
            "short_description": s.short_description,
            "featured_image_url": s.featured_image_url,
            "price_note": s.price_note,
            "tags": s.tags or [],
        } for s in services],
    })


@api_v1.get("/services/categories/<category_slug>/<service_slug>")
def public_get_service(category_slug, service_slug):
    svc = get_published_service(category_slug, service_slug)
    if not svc:
        raise NotFoundError("Service not found.")
    return ok({
        "slug": svc.slug,
        "name": svc.name,
        "short_description": svc.short_description,
        "long_description": svc.long_description,
        "featured_image_url": svc.featured_image_url,
        "gallery": svc.gallery or [],
        "price_note": svc.price_note,
        "tags": svc.tags or [],
        "seo_title": svc.seo_title,
        "seo_description": svc.seo_description,
        "category": {
            "slug": svc.category.slug,
            "name": svc.category.name,
        },
    })


# ─── Public: Packages ────────────────────────────────────────────────

@api_v1.get("/packages")
def public_list_packages():
    category = request.args.get("category")
    featured = request.args.get("featured") == "true"
    pkgs = list_published_packages(category_slug=category, featured_only=featured)
    return ok([{
        "id": str(p.id),
        "slug": p.slug,
        "name": p.name,
        "tagline": p.tagline,
        "short_description": p.short_description,
        "hero_image_url": p.hero_image_url,
        "price_amount": float(p.price_amount) if p.price_amount is not None else None,
        "price_note": p.price_note,
        "currency": p.currency,
        "min_guests": p.min_guests,
        "max_guests": p.max_guests,
        "duration_hours": p.duration_hours,
        "availability_note": p.availability_note,
        "is_featured": p.is_featured,
        "category": (
            {"slug": p.category.slug, "name": p.category.name}
            if p.category else None
        ),
    } for p in pkgs])


@api_v1.get("/packages/<slug>")
def public_get_package(slug):
    pkg = get_published_package(slug)
    if not pkg:
        raise NotFoundError("Package not found.")
    return ok({
        "id": str(pkg.id),
        "slug": pkg.slug,
        "name": pkg.name,
        "tagline": pkg.tagline,
        "short_description": pkg.short_description,
        "long_description": pkg.long_description,
        "what_is_included": pkg.what_is_included or [],
        "what_is_not_included": pkg.what_is_not_included or [],
        "hero_image_url": pkg.hero_image_url,
        "gallery": pkg.gallery or [],
        "price_amount": float(pkg.price_amount) if pkg.price_amount is not None else None,
        "price_note": pkg.price_note,
        "currency": pkg.currency,
        "min_guests": pkg.min_guests,
        "max_guests": pkg.max_guests,
        "duration_hours": pkg.duration_hours,
        "availability_note": pkg.availability_note,
        "is_featured": pkg.is_featured,
        "seo_title": pkg.seo_title,
        "seo_description": pkg.seo_description,
        "category": (
            {"slug": pkg.category.slug, "name": pkg.category.name}
            if pkg.category else None
        ),
        "services": [{
            "slug": s.slug,
            "name": s.name,
        } for s in pkg.services],
    })




    # admin services endpoints


    
from app.schemas import service_create_schema, service_update_schema
from app.services import create_service, update_service, publish_service, unpublish_service

@api_v1.get("/admin/services/categories")
@login_required
@require_permission("service.view")
def admin_list_service_categories():
    cats = ServiceCategory.query.order_by(ServiceCategory.sort_order.asc()).all()
    return ok([{
        "id": str(c.id),
        "slug": c.slug,
        "name": c.name,
        "short_description": c.short_description,
        "service_count": len(c.services),
        "published_count": len([s for s in c.services if s.is_published]),
    } for c in cats])


@api_v1.get("/admin/services")
@login_required
@require_permission("service.view")
def admin_list_services():
    q = Service.query
    if cid := request.args.get("category_id"):
        q = q.filter(Service.category_id == cid)
    if st := request.args.get("status"):
        if st == "published":
            q = q.filter(Service.is_published.is_(True))
        elif st == "draft":
            q = q.filter(Service.is_published.is_(False))
    services = q.order_by(Service.sort_order.asc()).all()



    print(f"[DEBUG] Services returned: {len(services)}")
    print(f"[DEBUG] Service IDs: {[str(s.id) for s in services]}")






    return ok([{
        "id": str(s.id),
        "category_id": str(s.category_id),
        "category_slug": s.category.slug,
        "slug": s.slug,
        "name": s.name,
        "short_description": s.short_description,
        "featured_image_url": s.featured_image_url,
        "price_note": s.price_note,
        "tags": s.tags or [],
        "sort_order": s.sort_order,
        "is_published": s.is_published,
        "published_at": s.published_at.isoformat() if s.published_at else None,
        "updated_at": s.updated_at.isoformat(),
    } for s in services])


@api_v1.post("/admin/services")
@login_required
@require_permission("service.create")
@idempotent
def admin_create_service():
    try:
        data = service_create_schema.load(request.get_json() or {})
    except ValidationError as exc:
        return _validation_error(exc)


    try:
        svc = create_service(
            category_id=data["category_id"],
            name=data["name"],
            short_description=data.get("short_description"),
            long_description=data.get("long_description"),
            featured_image_url=data.get("featured_image_url"),
            gallery=data.get("gallery"),
            price_note=data.get("price_note"),
            tags=data.get("tags"),
            sort_order=data.get("sort_order", 0),
            seo_title=data.get("seo_title"),
            seo_description=data.get("seo_description"),
        )
    except ValueError as exc:
        return error("conflict", str(exc), status=409)

    write_audit("service.created", entity_type="service",
                entity_id=str(svc.id), after={"slug": svc.slug})
    db.session.commit()
    return ok({"id": str(svc.id), "slug": svc.slug}, status=201)


@api_v1.patch("/admin/services/<uuid:service_id>")
@login_required
@require_permission("service.edit")
def admin_update_service(service_id):
    svc = Service.query.get(service_id)
    if not svc:
        raise NotFoundError("Service not found.")
    try:
        data = service_update_schema.load(request.get_json() or {}, partial=True)
    except ValidationError as exc:
        return _validation_error(exc)
    update_service(svc, data=data)
    write_audit("service.updated", entity_type="service", entity_id=str(svc.id))
    db.session.commit()
    return ok({"id": str(svc.id), "updated_at": svc.updated_at.isoformat()})


@api_v1.post("/admin/services/<uuid:service_id>/publish")
@login_required
@require_permission("service.publish")
def admin_publish_service(service_id):
    svc = Service.query.get(service_id)
    if not svc:
        raise NotFoundError("Service not found.")
    publish_service(svc, actor_user_id=g.current_user.id)
    write_audit("service.published", entity_type="service", entity_id=str(svc.id))
    db.session.commit()
    return ok({"is_published": svc.is_published})


@api_v1.post("/admin/services/<uuid:service_id>/unpublish")
@login_required
@require_permission("service.publish")
def admin_unpublish_service(service_id):
    svc = Service.query.get(service_id)
    if not svc:
        raise NotFoundError("Service not found.")
    unpublish_service(svc, actor_user_id=g.current_user.id)
    write_audit("service.unpublished", entity_type="service", entity_id=str(svc.id))
    db.session.commit()
    return ok({"is_published": svc.is_published})


@api_v1.delete("/admin/services/<uuid:service_id>")
@login_required
@require_permission("service.delete")
def admin_delete_service(service_id):
    svc = Service.query.get(service_id)
    if not svc:
        raise NotFoundError("Service not found.")
    write_audit("service.deleted", entity_type="service",
                entity_id=str(svc.id), before={"name": svc.name})
    db.session.delete(svc)
    db.session.commit()
    return ok({"id": service_id, "deleted": True})




# admin service crud operations

from app.services import (
    create_package, update_package,
    submit_package_for_review, approve_package, reject_package,
    unpublish_package, archive_package,
)
from app.schemas import (
    package_create_schema, package_update_schema, package_reject_schema,
)


@api_v1.get("/admin/packages")
@login_required
@require_permission("package.view")
def admin_list_packages():
    q = Package.query
    if st := request.args.get("status"):
        try:
            q = q.filter(Package.status == PackageStatus(st))
        except ValueError:
            return error("validation_error", "Invalid status.",
                         details={"allowed": [x.value for x in PackageStatus]},
                         status=422)
    pkgs = q.order_by(Package.updated_at.desc()).all()
    return ok([{
        "id": str(p.id),
        "slug": p.slug,
        "name": p.name,
        "status": p.status.value,
        "price_amount": float(p.price_amount) if p.price_amount is not None else None,
        "currency": p.currency,
        "category": (
            {"slug": p.category.slug, "name": p.category.name}
            if p.category else None
        ),
        "published_at": p.published_at.isoformat() if p.published_at else None,
        "submitted_at": p.submitted_at.isoformat() if p.submitted_at else None,
        "reviewed_at": p.reviewed_at.isoformat() if p.reviewed_at else None,
        "rejection_reason": p.rejection_reason,
        "updated_at": p.updated_at.isoformat(),
    } for p in pkgs])


@api_v1.get("/admin/packages/<uuid:package_id>")
@login_required
@require_permission("package.view")
def admin_get_package(package_id):
    p = Package.query.get(package_id)
    if not p:
        raise NotFoundError("Package not found.")
    return ok({
        "id": str(p.id),
        "slug": p.slug,
        "name": p.name,
        "tagline": p.tagline,
        "short_description": p.short_description,
        "long_description": p.long_description,
        "what_is_included": p.what_is_included or [],
        "what_is_not_included": p.what_is_not_included or [],
        "hero_image_url": p.hero_image_url,
        "gallery": p.gallery or [],
        "category_id": str(p.category_id) if p.category_id else None,
        "price_amount": float(p.price_amount) if p.price_amount is not None else None,
        "price_note": p.price_note,
        "currency": p.currency,
        "min_guests": p.min_guests,
        "max_guests": p.max_guests,
        "duration_hours": p.duration_hours,
        "availability_note": p.availability_note,
        "status": p.status.value,
        "is_featured": p.is_featured,
        "seo_title": p.seo_title,
        "seo_description": p.seo_description,
        "rejection_reason": p.rejection_reason,
        "created_by": (
            {"id": str(p.created_by.id), "full_name": p.created_by.full_name}
            if p.created_by else None
        ),
        "reviewed_by": (
            {"id": str(p.reviewed_by.id), "full_name": p.reviewed_by.full_name}
            if p.reviewed_by else None
        ),
        "created_at": p.created_at.isoformat(),
        "updated_at": p.updated_at.isoformat(),

        "inventory_items": [
            {
                "inventory_item_id": str(pi.inventory_item_id),
                "name": pi.inventory_item.name,
                "quantity": pi.quantity,
                "notes": pi.notes,
            }
            for pi in p.inventory_items
        ],
    })


@api_v1.post("/admin/packages")
@login_required
@require_permission("package.create")
@idempotent
def admin_create_package():
    try:
        data = package_create_schema.load(request.get_json() or {})
    except ValidationError as exc:
        return _validation_error(exc)

    try:
        pkg = create_package(
            name=data["name"],
            created_by_user_id=g.current_user.id,
            tagline=data.get("tagline"),
            short_description=data.get("short_description"),
            long_description=data.get("long_description"),
            what_is_included=data.get("what_is_included"),
            what_is_not_included=data.get("what_is_not_included"),
            hero_image_url=data.get("hero_image_url"),
            gallery=data.get("gallery"),
            category_id=data.get("category_id"),
            price_amount=data.get("price_amount"),
            price_note=data.get("price_note"),
            currency=data.get("currency", "KES"),
            min_guests=data.get("min_guests"),
            max_guests=data.get("max_guests"),
            duration_hours=data.get("duration_hours"),
            availability_note=data.get("availability_note"),
            is_featured=data.get("is_featured", False),
            seo_title=data.get("seo_title"),
            seo_description=data.get("seo_description"),
        )
    except ValueError as exc:
        return error("conflict", str(exc), status=409)

    write_audit("package.created", entity_type="package",
                entity_id=str(pkg.id), after={"slug": pkg.slug})
    db.session.commit()
    return ok({"id": str(pkg.id), "slug": pkg.slug, "status": pkg.status.value},
              status=201)


@api_v1.patch("/admin/packages/<uuid:package_id>")
@login_required
@require_permission("package.edit")
def admin_update_package(package_id):
    pkg = Package.query.get(package_id)
    if not pkg:
        raise NotFoundError("Package not found.")
    try:
        data = package_update_schema.load(request.get_json() or {}, partial=True)
    except ValidationError as exc:
        return _validation_error(exc)
    try:
        update_package(pkg, data=data)
    except ValueError as exc:
        return error("invalid_state", str(exc), status=409)
    write_audit("package.updated", entity_type="package", entity_id=str(pkg.id))
    db.session.commit()
    return ok({"id": str(pkg.id), "updated_at": pkg.updated_at.isoformat()})


@api_v1.post("/admin/packages/<uuid:package_id>/submit")
@login_required
@require_permission("package.submit")
def admin_submit_package(package_id):
    pkg = Package.query.get(package_id)
    if not pkg:
        raise NotFoundError("Package not found.")
    try:
        submit_package_for_review(pkg, actor_user_id=g.current_user.id)
    except ValueError as exc:
        return error("invalid_state", str(exc), status=409)
    write_audit("package.submitted", entity_type="package", entity_id=str(pkg.id))
    db.session.commit()
    emit_alert("package.submitted",
               {"id": str(pkg.id), "name": pkg.name},
               room=ROOM_ADMINS)
    return ok({"status": pkg.status.value})


@api_v1.post("/admin/packages/<uuid:package_id>/approve")
@login_required
@require_permission("package.approve")
def admin_approve_package(package_id):
    pkg = Package.query.get(package_id)
    if not pkg:
        raise NotFoundError("Package not found.")
    try:
        approve_package(pkg, actor_user_id=g.current_user.id)
    except ValueError as exc:
        return error("invalid_state", str(exc), status=409)
    write_audit("package.approved", entity_type="package", entity_id=str(pkg.id))
    db.session.commit()
    return ok({"status": pkg.status.value,
               "published_at": pkg.published_at.isoformat()})


@api_v1.post("/admin/packages/<uuid:package_id>/reject")
@login_required
@require_permission("package.approve")
def admin_reject_package(package_id):
    pkg = Package.query.get(package_id)
    if not pkg:
        raise NotFoundError("Package not found.")
    try:
        data = package_reject_schema.load(request.get_json() or {})
    except ValidationError as exc:
        return _validation_error(exc)
    try:
        reject_package(pkg, reason=data["reason"], actor_user_id=g.current_user.id)
    except ValueError as exc:
        return error("invalid_state", str(exc), status=409)
    write_audit("package.rejected", entity_type="package", entity_id=str(pkg.id),
                after={"reason": data["reason"]})
    db.session.commit()
    return ok({"status": pkg.status.value})




# @api_v1.post("/admin/packages/upload-image")
# @login_required
# def admin_upload_package_image():
#     if not (
#         g.current_user.has_permission("package.create")
#         or g.current_user.has_permission("package.edit")
#     ):
#         return error(
#             "forbidden",
#             "You do not have permission to upload package images.",
#             status=403,
#         )

#     if "file" not in request.files:
#         return error(
#             "validation_error",
#             "No file provided.",
#             status=422,
#         )

#     uploaded_file = request.files["file"]

#     if not uploaded_file.filename:
#         return error(
#             "validation_error",
#             "No file selected.",
#             status=422,
#         )

#     try:
#         image = process_and_store_image(
#             file_bytes=uploaded_file.read(),
#             mime_type=uploaded_file.mimetype or "application/octet-stream",
#             prefix="packages",
#         )
#     except ValueError as exc:
#         return error("validation_error", str(exc), status=422)

#     return ok({
#         "url": image["url"],
#         "thumb_url": image["thumb_url"],
#         "width": image["width"],
#         "height": image["height"],
#         "size_bytes": image["size_bytes"],
#     }, status=201)




@api_v1.post("/admin/packages/<uuid:package_id>/unpublish")
@login_required
@require_permission("package.publish")
def admin_unpublish_package(package_id):
    pkg = Package.query.get(package_id)
    if not pkg:
        raise NotFoundError("Package not found.")
    try:
        unpublish_package(pkg, actor_user_id=g.current_user.id)
    except ValueError as exc:
        return error("invalid_state", str(exc), status=409)
    write_audit("package.unpublished", entity_type="package", entity_id=str(pkg.id))
    db.session.commit()
    return ok({"status": pkg.status.value})


@api_v1.post("/admin/packages/<uuid:package_id>/archive")
@login_required
@require_permission("package.publish")
def admin_archive_package(package_id):
    pkg = Package.query.get(package_id)
    if not pkg:
        raise NotFoundError("Package not found.")
    archive_package(pkg, actor_user_id=g.current_user.id)
    write_audit("package.archived", entity_type="package", entity_id=str(pkg.id))
    db.session.commit()
    return ok({"status": pkg.status.value})







from app.models import InventoryCategory, InventoryItem, PackageInventoryItem
from app.services import (
    list_inventory_categories, create_inventory_category, update_inventory_category,
    list_inventory_items, create_inventory_item, update_inventory_item,
    publish_inventory_item, unpublish_inventory_item, delete_inventory_item,
    set_package_inventory,
)
from app.schemas import (
    inventory_category_schema, inventory_item_create_schema,
    inventory_item_update_schema, inventory_links_replace_schema,
)


# ─── Public ─────────────────────────────────────────────────────────

@api_v1.get("/inventory/categories")
def public_list_inventory_categories():
    cats = list_inventory_categories()
    return ok([{
        "slug": c.slug, "name": c.name,
        "short_description": c.short_description,
        "icon": c.icon,
        "published_item_count": len([i for i in c.items if i.is_published]),
    } for c in cats])


@api_v1.get("/inventory")
def public_list_inventory():
    category = request.args.get("category")
    if category:
        cat = InventoryCategory.query.filter_by(slug=category).first()
        items = list_inventory_items(category_id=cat.id, published_only=True) if cat else []
    else:
        items = list_inventory_items(published_only=True)
    return ok([{
        "id": str(i.id),
        "slug": i.slug,
        "name": i.name,
        "short_description": i.short_description,
        "featured_image_url": i.featured_image_url,
        "unit_price_hint": float(i.unit_price_hint) if i.unit_price_hint is not None else None,
        "unit": i.unit,
        "currency": i.currency,
        "quantity_owned": i.quantity_owned,
        "category": {"slug": i.category.slug, "name": i.category.name},
    } for i in items])


# ─── Admin: categories ──────────────────────────────────────────────

@api_v1.get("/admin/inventory/categories")
@login_required
@require_permission("inventory.view")
def admin_list_inventory_categories():
    cats = list_inventory_categories()
    return ok([{
        "id": str(c.id), "slug": c.slug, "name": c.name,
        "short_description": c.short_description,
        "icon": c.icon, "sort_order": c.sort_order,
        "item_count": len(c.items),
    } for c in cats])


@api_v1.post("/admin/inventory/categories")
@login_required
@require_permission("inventory.create")
@idempotent
def admin_create_inventory_category():
    try:
        data = inventory_category_schema.load(request.get_json() or {})
    except ValidationError as exc:
        return _validation_error(exc)
    try:
        cat = create_inventory_category(**data)
    except ValueError as exc:
        return error("conflict", str(exc), status=409)
    write_audit("inventory_category.created", entity_type="inventory_category",
                entity_id=str(cat.id))
    db.session.commit()
    return ok({"id": str(cat.id), "slug": cat.slug}, status=201)


@api_v1.patch("/admin/inventory/categories/<uuid:cat_id>")
@login_required
@require_permission("inventory.edit")
def admin_update_inventory_category(cat_id):
    cat = InventoryCategory.query.get(cat_id)
    if not cat:
        raise NotFoundError("Category not found.")
    try:
        data = inventory_category_schema.load(request.get_json() or {}, partial=True)
    except ValidationError as exc:
        return _validation_error(exc)
    update_inventory_category(cat, data=data)
    db.session.commit()
    return ok({"id": str(cat.id)})


@api_v1.delete("/admin/inventory/categories/<uuid:cat_id>")
@login_required
@require_permission("inventory.delete")
def admin_delete_inventory_category(cat_id):
    """
    Delete a category only if no inventory items reference it.
    Returns 409 with details if the category is still in use.
    """
    cat = InventoryCategory.query.get(cat_id)
    if not cat:
        raise NotFoundError("Category not found.")

    item_count = InventoryItem.query.filter_by(category_id=cat.id).count()
    if item_count > 0:
        return error(
            "category_in_use",
            f"This category contains {item_count} inventory item"
            f"{'s' if item_count != 1 else ''}. "
            "Move or delete them first.",
            details={
                "item_count": item_count,
                "category_id": str(cat.id),
                "category_slug": cat.slug,
            },
            status=409,
        )

    write_audit("inventory_category.deleted",
                entity_type="inventory_category",
                entity_id=str(cat.id),
                before={"slug": cat.slug, "name": cat.name})
    db.session.delete(cat)
    db.session.commit()
    return ok({"id": str(cat.id), "deleted": True})


@api_v1.post("/admin/inventory/categories/reorder")
@login_required
@require_permission("inventory.edit")
def admin_reorder_inventory_categories():
    """
    Optional: accept {items: [{id, sort_order}, ...]} and update in bulk.
    """
    body = request.get_json() or {}
    items = body.get("items", [])
    for row in items:
        cat = InventoryCategory.query.get(row.get("id"))
        if cat:
            cat.sort_order = int(row.get("sort_order", 0))
    db.session.commit()
    return ok({"updated": len(items)})




# ─── Admin: items ───────────────────────────────────────────────────

@api_v1.get("/admin/inventory")
@login_required
@require_permission("inventory.view")
def admin_list_inventory():
    category_id = request.args.get("category_id")
    search = request.args.get("q")
    items = list_inventory_items(category_id=category_id, search=search)
    return ok([{
        "id": str(i.id),
        "category_id": str(i.category_id),
        "category_slug": i.category.slug,
        "slug": i.slug,
        "name": i.name,
        "short_description": i.short_description,
        "quantity_owned": i.quantity_owned,
        "quantity_available_note": i.quantity_available_note,
        "unit_price_hint": float(i.unit_price_hint) if i.unit_price_hint is not None else None,
        "unit": i.unit,
        "currency": i.currency,
        "featured_image_url": i.featured_image_url,
        "is_published": i.is_published,
        "sort_order": i.sort_order,
    } for i in items])


@api_v1.get("/admin/inventory/<uuid:item_id>")
@login_required
@require_permission("inventory.view")
def admin_get_inventory_item(item_id):
    item = InventoryItem.query.get(item_id)
    if not item:
        raise NotFoundError("Item not found.")
    return ok({
        "id": str(item.id),
        "category_id": str(item.category_id),
        "slug": item.slug,
        "name": item.name,
        "short_description": item.short_description,
        "long_description": item.long_description,
        "quantity_owned": item.quantity_owned,
        "quantity_available_note": item.quantity_available_note,
        "unit_price_hint": float(item.unit_price_hint) if item.unit_price_hint is not None else None,
        "unit": item.unit,
        "currency": item.currency,
        "featured_image_url": item.featured_image_url,
        "gallery": item.gallery or [],
        "tags": item.tags or [],
        "is_published": item.is_published,
        "sort_order": item.sort_order,
        "seo_title": item.seo_title,
        "seo_description": item.seo_description,
    })


@api_v1.post("/admin/inventory")
@login_required
@require_permission("inventory.create")
@idempotent
def admin_create_inventory_item():
    try:
        data = inventory_item_create_schema.load(request.get_json() or {})
    except ValidationError as exc:
        return _validation_error(exc)
    try:
        item = create_inventory_item(
            category_id=data["category_id"],
            name=data["name"],
            short_description=data.get("short_description"),
            long_description=data.get("long_description"),
            quantity_owned=data.get("quantity_owned", 0),
            quantity_available_note=data.get("quantity_available_note"),
            unit_price_hint=data.get("unit_price_hint"),
            unit=data.get("unit"),
            currency=data.get("currency", "KES"),
            featured_image_url=data.get("featured_image_url"),
            gallery=data.get("gallery"),
            tags=data.get("tags"),
            sort_order=data.get("sort_order", 0),
            seo_title=data.get("seo_title"),
            seo_description=data.get("seo_description"),
        )
    except ValueError as exc:
        return error("conflict", str(exc), status=409)
    write_audit("inventory_item.created", entity_type="inventory_item",
                entity_id=str(item.id))
    db.session.commit()
    return ok({"id": str(item.id), "slug": item.slug}, status=201)


@api_v1.patch("/admin/inventory/<uuid:item_id>")
@login_required
@require_permission("inventory.edit")
def admin_update_inventory_item(item_id):
    item = InventoryItem.query.get(item_id)
    if not item:
        raise NotFoundError("Item not found.")
    try:
        data = inventory_item_update_schema.load(request.get_json() or {}, partial=True)
    except ValidationError as exc:
        return _validation_error(exc)
    update_inventory_item(item, data=data)
    write_audit("inventory_item.updated", entity_type="inventory_item",
                entity_id=str(item.id))
    db.session.commit()
    return ok({"id": str(item.id)})


@api_v1.post("/admin/inventory/<uuid:item_id>/publish")
@login_required
@require_permission("inventory.publish")
def admin_publish_inventory_item(item_id):
    item = InventoryItem.query.get(item_id)
    if not item:
        raise NotFoundError("Item not found.")
    publish_inventory_item(item, actor_user_id=g.current_user.id)
    db.session.commit()
    return ok({"is_published": True})


@api_v1.post("/admin/inventory/<uuid:item_id>/unpublish")
@login_required
@require_permission("inventory.publish")
def admin_unpublish_inventory_item(item_id):
    item = InventoryItem.query.get(item_id)
    if not item:
        raise NotFoundError("Item not found.")
    unpublish_inventory_item(item, actor_user_id=g.current_user.id)
    db.session.commit()
    return ok({"is_published": False})


@api_v1.delete("/admin/inventory/<uuid:item_id>")
@login_required
@require_permission("inventory.delete")
def admin_delete_inventory_item(item_id):
    item = InventoryItem.query.get(item_id)
    if not item:
        raise NotFoundError("Item not found.")

    # Check for links
    pkg_refs = PackageInventoryItem.query.filter_by(inventory_item_id=item.id).count()
    total_refs = pkg_refs

    if total_refs > 0:
        return error(
            "item_in_use",
            f"This item is referenced by {total_refs} record"
            f"{'s' if total_refs != 1 else ''}. Remove it from those first.",
            details={
                "packages": pkg_refs,
                "total": total_refs,
            },
            status=409,
        )

    write_audit("inventory_item.deleted", entity_type="inventory_item",
                entity_id=str(item.id), before={"name": item.name})
    db.session.delete(item)
    db.session.commit()
    return ok({"deleted": True})





def _upload_inventory_image():
    if "file" not in request.files:
        return error(
            "validation_error",
            "No file provided.",
            details={"field": "file"},
            status=422,
        )

    f = request.files["file"]

    if not f.filename:
        return error(
            "validation_error",
            "Empty filename.",
            details={"field": "file"},
            status=422,
        )

    try:
        image = process_and_store_image(
            file_bytes=f.read(),
            mime_type=f.mimetype or "image/jpeg",
            prefix="inventory",
        )
    except ValueError as exc:
        return error("validation_error", str(exc), status=422)

    return ok({
        "url": image["url"],
        "thumb_url": image["thumb_url"],
        "width": image["width"],
        "height": image["height"],
        "size_bytes": image["size_bytes"],
    }, status=201)











@api_v1.post("/admin/inventory/upload-image")
@login_required
@require_permission("inventory.create")
def admin_upload_inventory_image_create():
    return _upload_inventory_image()


@api_v1.post("/admin/inventory/upload-image/edit")
@login_required
@require_permission("inventory.edit")
def admin_upload_inventory_image_edit():
    return _upload_inventory_image()












# ─── Package ↔ Inventory link ──────────────────────────────────────

@api_v1.put("/admin/packages/<uuid:package_id>/inventory")
@login_required
@require_permission("package.edit")
@idempotent
def admin_replace_package_inventory(package_id):
    pkg = Package.query.get(package_id)
    if not pkg:
        raise NotFoundError("Package not found.")
    try:
        data = inventory_links_replace_schema.load(request.get_json() or {})
    except ValidationError as exc:
        return _validation_error(exc)
    set_package_inventory(pkg, data["items"])
    write_audit("package.inventory_replaced", entity_type="package",
                entity_id=str(pkg.id))
    db.session.commit()
    return ok({"count": len(data["items"])})



from app.models import GalleryAlbum, GalleryImage
from app.services import (
    create_gallery_album, update_gallery_album,
    publish_gallery_album, unpublish_gallery_album, delete_gallery_album,
    create_gallery_image, update_gallery_image,
    publish_gallery_image, unpublish_gallery_image, delete_gallery_image,
    reorder_gallery_images, list_public_gallery,
)


# ─── Public ─────────────────────────────────────────────────────────

@api_v1.get("/gallery")
def public_gallery():
    category = request.args.get("category")
    album = request.args.get("album")
    limit = min(int(request.args.get("limit", 100)), 500)

    images = list_public_gallery(
        category_slug=category,
        album_slug=album,
        limit=limit,
    )
    return ok([{
        "id": str(i.id),
        "url": i.url,
        "thumb_url": i.thumb_url if hasattr(i, "thumb_url") else i.url.replace(".webp", "_thumb.webp"),
        "alt_text": i.alt_text,
        "caption": i.caption,
        "width": i.width,
        "height": i.height,
        "is_featured": i.is_featured,
        "album": (
            {"slug": i.album.slug, "name": i.album.name}
            if i.album else None
        ),
    } for i in images])


@api_v1.get("/gallery/albums")
def public_gallery_albums():
    albums = GalleryAlbum.query.filter_by(is_published=True).order_by(
        GalleryAlbum.sort_order.asc()
    ).all()
    return ok([{
        "slug": a.slug,
        "name": a.name,
        "description": a.description,
        "cover_image_url": a.cover_image_url,
        "image_count": len([i for i in a.images if i.is_published]),
        "category": (
            {"slug": a.category.slug, "name": a.category.name}
            if a.category else None
        ),
    } for a in albums])


@api_v1.get("/gallery/files/<path:key>")
def serve_gallery_file(key):
    """Serve gallery images from local storage."""
    from flask import send_file
    from io import BytesIO
    from app.storage import get_storage

    if ".." in key or key.startswith("/"):
        raise NotFoundError("Invalid path.")

    try:
        data = get_storage().read(key)
    except Exception:
        raise NotFoundError("File not found.")

    ext = key.rsplit(".", 1)[-1].lower() if "." in key else "webp"
    mime = {
        "webp": "image/webp",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
    }.get(ext, "application/octet-stream")

    resp = send_file(BytesIO(data), mimetype=mime)
    resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    return resp


# ─── Admin: albums ──────────────────────────────────────────────────

@api_v1.get("/admin/gallery/albums")
@login_required
@require_permission("gallery.view")
def admin_list_albums():
    albums = GalleryAlbum.query.order_by(GalleryAlbum.sort_order.asc()).all()
    return ok([{
        "id": str(a.id),
        "slug": a.slug,
        "name": a.name,
        "description": a.description,
        "category_id": str(a.category_id) if a.category_id else None,
        "cover_image_url": a.cover_image_url,
        "is_published": a.is_published,
        "sort_order": a.sort_order,
        "image_count": len(a.images),
        "published_count": len([i for i in a.images if i.is_published]),
    } for a in albums])


@api_v1.post("/admin/gallery/albums")
@login_required
@require_permission("gallery.create")
@idempotent
def admin_create_album():
    body = request.get_json() or {}
    name = (body.get("name") or "").strip()
    if len(name) < 2:
        return error("validation_error", "Album name is required.",
                     details={"field": "name"}, status=422)
    try:
        album = create_gallery_album(
            name=name,
            slug=body.get("slug"),
            description=body.get("description"),
            category_id=body.get("category_id"),
            sort_order=body.get("sort_order", 0),
            seo_title=body.get("seo_title"),
            seo_description=body.get("seo_description"),
        )
    except ValueError as exc:
        return error("conflict", str(exc), status=409)
    write_audit("gallery_album.created", entity_type="gallery_album",
                entity_id=str(album.id))
    db.session.commit()
    return ok({"id": str(album.id), "slug": album.slug}, status=201)


@api_v1.patch("/admin/gallery/albums/<uuid:album_id>")
@login_required
@require_permission("gallery.edit")
def admin_update_album(album_id):
    album = GalleryAlbum.query.get(album_id)
    if not album:
        raise NotFoundError("Album not found.")
    update_gallery_album(album, data=request.get_json() or {})
    write_audit("gallery_album.updated", entity_type="gallery_album",
                entity_id=str(album.id))
    db.session.commit()
    return ok({"id": str(album.id)})


@api_v1.post("/admin/gallery/albums/<uuid:album_id>/publish")
@login_required
@require_permission("gallery.publish")
def admin_publish_album(album_id):
    album = GalleryAlbum.query.get(album_id)
    if not album:
        raise NotFoundError("Album not found.")
    publish_gallery_album(album, actor_user_id=g.current_user.id)
    db.session.commit()
    return ok({"is_published": True})


@api_v1.post("/admin/gallery/albums/<uuid:album_id>/unpublish")
@login_required
@require_permission("gallery.publish")
def admin_unpublish_album(album_id):
    album = GalleryAlbum.query.get(album_id)
    if not album:
        raise NotFoundError("Album not found.")
    unpublish_gallery_album(album, actor_user_id=g.current_user.id)
    db.session.commit()
    return ok({"is_published": False})


@api_v1.delete("/admin/gallery/albums/<uuid:album_id>")
@login_required
@require_permission("gallery.delete")
def admin_delete_album(album_id):
    album = GalleryAlbum.query.get(album_id)
    if not album:
        raise NotFoundError("Album not found.")
    write_audit("gallery_album.deleted", entity_type="gallery_album",
                entity_id=str(album.id), before={"name": album.name})
    delete_gallery_album(album)
    db.session.commit()
    return ok({"deleted": True})


# ─── Admin: images ──────────────────────────────────────────────────

@api_v1.get("/admin/gallery/images")
@login_required
@require_permission("gallery.view")
def admin_list_gallery_images():
    q = GalleryImage.query
    if album_id := request.args.get("album_id"):
        q = q.filter(GalleryImage.album_id == album_id)
    if cat_id := request.args.get("category_id"):
        q = q.filter(GalleryImage.category_id == cat_id)
    if request.args.get("unpublished") == "true":
        q = q.filter(GalleryImage.is_published.is_(False))

    images = q.order_by(GalleryImage.sort_order.asc()).limit(500).all()
    return ok([{
        "id": str(i.id),
        "url": i.url,
        "thumb_url": i.url.replace(".webp", "_thumb.webp") if i.url.endswith(".webp") else i.url,
        "alt_text": i.alt_text,
        "caption": i.caption,
        "album_id": str(i.album_id) if i.album_id else None,
        "category_id": str(i.category_id) if i.category_id else None,
        "width": i.width,
        "height": i.height,
        "size_bytes": i.size_bytes,
        "is_published": i.is_published,
        "is_featured": i.is_featured,
        "sort_order": i.sort_order,
        "created_at": i.created_at.isoformat(),
    } for i in images])


@api_v1.post("/admin/gallery/images")
@login_required
@require_permission("gallery.create")
@idempotent
def admin_upload_gallery_image():
    """
    Multipart upload. Fields:
      file        (required)
      alt_text    (required)
      caption     (optional)
      album_id    (optional)
      category_id (optional)
    """
    if "file" not in request.files:
        return error("validation_error", "No file provided.",
                     details={"field": "file"}, status=422)

    f = request.files["file"]
    if not f.filename:
        return error("validation_error", "Empty filename.", status=422)

    alt_text = (request.form.get("alt_text") or "").strip()
    if not alt_text:
        return error("validation_error", "Alt text is required.",
                     details={"field": "alt_text"}, status=422)

    try:
        img = create_gallery_image(
            file_bytes=f.read(),
            mime_type=f.mimetype or "image/jpeg",
            alt_text=alt_text,
            caption=request.form.get("caption"),
            album_id=request.form.get("album_id") or None,
            category_id=request.form.get("category_id") or None,
            uploaded_by_user_id=g.current_user.id,
        )
    except ValueError as exc:
        return error("validation_error", str(exc), status=422)

    write_audit("gallery_image.uploaded", entity_type="gallery_image",
                entity_id=str(img.id), after={"alt_text": alt_text})
    db.session.commit()
    return ok({
        "id": str(img.id),
        "url": img.url,
        "thumb_url": img.url.replace(".webp", "_thumb.webp"),
    }, status=201)


@api_v1.patch("/admin/gallery/images/<uuid:image_id>")
@login_required
@require_permission("gallery.edit")
def admin_update_gallery_image(image_id):
    img = GalleryImage.query.get(image_id)
    if not img:
        raise NotFoundError("Image not found.")
    update_gallery_image(img, data=request.get_json() or {})
    write_audit("gallery_image.updated", entity_type="gallery_image",
                entity_id=str(img.id))
    db.session.commit()
    return ok({"id": str(img.id)})


@api_v1.post("/admin/gallery/images/<uuid:image_id>/publish")
@login_required
@require_permission("gallery.publish")
def admin_publish_gallery_image(image_id):
    img = GalleryImage.query.get(image_id)
    if not img:
        raise NotFoundError("Image not found.")
    publish_gallery_image(img, actor_user_id=g.current_user.id)
    db.session.commit()
    return ok({"is_published": True})


@api_v1.post("/admin/gallery/images/<uuid:image_id>/unpublish")
@login_required
@require_permission("gallery.publish")
def admin_unpublish_gallery_image(image_id):
    img = GalleryImage.query.get(image_id)
    if not img:
        raise NotFoundError("Image not found.")
    unpublish_gallery_image(img, actor_user_id=g.current_user.id)
    db.session.commit()
    return ok({"is_published": False})


@api_v1.delete("/admin/gallery/images/<uuid:image_id>")
@login_required
@require_permission("gallery.delete")
def admin_delete_gallery_image(image_id):
    img = GalleryImage.query.get(image_id)
    if not img:
        raise NotFoundError("Image not found.")
    write_audit("gallery_image.deleted", entity_type="gallery_image",
                entity_id=str(img.id), before={"alt_text": img.alt_text})
    delete_gallery_image(img)
    db.session.commit()
    return ok({"deleted": True})


@api_v1.post("/admin/gallery/images/reorder")
@login_required
@require_permission("gallery.edit")
def admin_reorder_gallery():
    body = request.get_json() or {}
    items = body.get("items", [])  # [{"id": "...", "sort_order": 10}, ...]
    reorder_gallery_images([(i["id"], i["sort_order"]) for i in items if i.get("id")])
    db.session.commit()
    return ok({"updated": len(items)})



from app.models import Setting, SettingCategory, SettingRevision
from app.services import list_settings, get_setting, update_setting, create_setting
from app.schemas import setting_update_schema, setting_create_schema


# ─── Public policies (unauthenticated) ──────────────────────────────

@api_v1.get("/settings/policies/<key>")
def public_get_policy(key):
    """Fetch a published policy by key. No auth required."""
    s = Setting.query.filter_by(key=key, category=SettingCategory.POLICY).first()
    if not s or not s.is_published:
        raise NotFoundError("Policy not found.")
    return ok({
        "key": s.key,
        "label": s.label,
        "value_text": s.value_text,
        "updated_at": s.updated_at.isoformat(),
    })




# ─── Public: safe settings whitelist ────────────────────────────────

PUBLIC_SETTING_KEYS = (
    "company_name",
    "company_phone",
    "company_email",
    "company_address",
    "company_hours",
    "social_facebook",
    "social_instagram",
    "social_tiktok",
    "social_twitter",
)


@api_v1.get("/settings/public")
@limiter.limit("120 per minute")
def public_get_settings():
    """
    Returns only whitelisted, published settings. No auth.
    The frontend reads company_phone to build WhatsApp links.
    """
    rows = (
        Setting.query
        .filter(
            Setting.is_published.is_(True),
            Setting.key.in_(PUBLIC_SETTING_KEYS),
        )
        .all()
    )
    return ok({s.key: s.value_text for s in rows})





# ─── Admin settings list ────────────────────────────────────────────

@api_v1.get("/admin/settings")
@login_required
@require_permission("settings.view")
def admin_list_settings():
    cat = request.args.get("category")
    category_enum = None
    if cat:
        try:
            category_enum = SettingCategory(cat)
        except ValueError:
            return error("validation_error", "Invalid category.", status=422)
    rows = list_settings(category=category_enum)
    return ok([{
        "id": str(s.id),
        "key": s.key,
        "label": s.label,
        "category": s.category.value,
        "value_text": s.value_text,
        "description": s.description,
        "is_system": s.is_system,
        "is_published": s.is_published,
        "version": s.version,
        "updated_at": s.updated_at.isoformat(),
    } for s in rows])


@api_v1.get("/admin/settings/<key>")
@login_required
@require_permission("settings.view")
def admin_get_setting(key):
    s = Setting.query.filter_by(key=key).first()
    if not s:
        raise NotFoundError("Setting not found.")
    revisions = (SettingRevision.query
                 .filter_by(setting_id=s.id)
                 .order_by(SettingRevision.created_at.desc())
                 .limit(20).all())
    return ok({
        "id": str(s.id),
        "key": s.key,
        "label": s.label,
        "category": s.category.value,
        "value_text": s.value_text,
        "description": s.description,
        "is_system": s.is_system,
        "is_published": s.is_published,
        "version": s.version,
        "updated_at": s.updated_at.isoformat(),
        "revisions": [{
            "version": r.version,
            "value_text": r.value_text,
            "changed_by_user_id": str(r.changed_by_user_id) if r.changed_by_user_id else None,
            "created_at": r.created_at.isoformat(),
        } for r in revisions],
    })


@api_v1.patch("/admin/settings/<key>")
@login_required
@require_permission("settings.edit")
def admin_update_setting(key):
    s = Setting.query.filter_by(key=key).first()
    if not s:
        raise NotFoundError("Setting not found.")
    try:
        data = setting_update_schema.load(request.get_json() or {}, partial=True)
    except ValidationError as exc:
        return _validation_error(exc)

    update_setting(
        s,
        value_text=data.get("value_text", s.value_text),
        label=data.get("label"),
        is_published=data.get("is_published"),
        actor_user_id=g.current_user.id,
    )
    write_audit("setting.updated", entity_type="setting",
                entity_id=str(s.id), after={"key": s.key, "version": s.version})
    db.session.commit()
    return ok({"id": str(s.id), "version": s.version, "updated_at": s.updated_at.isoformat()})


@api_v1.post("/admin/settings")
@login_required
@require_permission("settings.edit")
@idempotent
def admin_create_setting():
    try:
        data = setting_create_schema.load(request.get_json() or {})
    except ValidationError as exc:
        return _validation_error(exc)
    try:
        s = create_setting(
            key=data["key"],
            label=data["label"],
            category=SettingCategory(data["category"]),
            value_text=data.get("value_text"),
            description=data.get("description"),
            is_system=False,
            actor_user_id=g.current_user.id,
        )
    except ValueError as exc:
        return error("conflict", str(exc), status=409)
    write_audit("setting.created", entity_type="setting", entity_id=str(s.id))
    db.session.commit()
    return ok({"id": str(s.id), "key": s.key}, status=201)


@api_v1.delete("/admin/settings/<key>")
@login_required
@require_permission("settings.edit")
def admin_delete_setting(key):
    s = Setting.query.filter_by(key=key).first()
    if not s:
        raise NotFoundError("Setting not found.")
    if s.is_system:
        return error("forbidden", "System settings cannot be deleted.", status=403)
    write_audit("setting.deleted", entity_type="setting",
                entity_id=str(s.id), before={"key": s.key})
    db.session.delete(s)
    db.session.commit()
    return ok({"deleted": True})






from app.services import analytics_overview, track_page_view


# ─── Public tracking ────────────────────────────────────────────────

@api_v1.post("/track")
def public_track_view():
    """
    Called by the frontend router on every navigation.
    No auth required.
    """
    body = request.get_json(silent=True) or {}
    session_id = body.get("session_id") or request.cookies.get("fw_session")
    if not session_id:
        import uuid as _uuid
        session_id = str(_uuid.uuid4())
    if not session_id or len(session_id) > 64:
        return ok({"skipped": True})

    path = (body.get("path") or "/")[:500]
    referrer = (body.get("referrer") or "")[:500] or None
    ip = request.headers.get("X-Forwarded-For", request.remote_addr or "").split(",")[0].strip()
    ua = request.headers.get("User-Agent", "")[:500]

    user_id = None
    if hasattr(g, "current_user") and g.current_user:
        user_id = g.current_user.id

    try:
        track_page_view(
            session_id=session_id,
            path=path,
            referrer=referrer,
            ip=ip,
            user_agent=ua,
            user_id=user_id,
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("track_view_failed")
        return ok({"ok": False})

    resp = ok({"ok": True, "session_id": session_id})
    resp[0].set_cookie("fw_session", session_id, max_age=1800, httponly=True, samesite="Lax")
    return resp


# ─── Admin analytics ────────────────────────────────────────────────

@api_v1.get("/admin/analytics/overview")
@login_required
@require_permission("settings.view")
def admin_analytics_overview():
    days = int(request.args.get("days", 30))
    days = max(1, min(days, 365))
    return ok(analytics_overview(days=days))

from app.models import VisitorSession, PageView

@api_v1.get("/admin/analytics/sessions")
@login_required
@require_permission("settings.view")
def admin_analytics_sessions():
    from sqlalchemy import desc
    limit = min(int(request.args.get("limit", 100)), 500)
    rows = (VisitorSession.query
            .order_by(VisitorSession.first_seen_at.desc())
            .limit(limit).all())
    return ok([{
        "session_id": r.session_id[:12] + "…",
        "country": r.country,
        "city": r.city,
        "referrer": r.referrer,
        "page_count": r.page_count,
        "first_seen_at": r.first_seen_at.isoformat(),
        "last_seen_at": r.last_seen_at.isoformat(),
    } for r in rows])





# ─── Public: Rentals (Items for Hire) ───────────────────────────────
from app.services import get_public_whatsapp_phone

@api_v1.get("/rentals")
@limiter.limit("120 per minute")
def public_list_rentals():
    """
    Public rentals index. Two modes:

      A) No filters → returns the list of rental categories (nav landing).
      B) ?category=<slug> → returns published items in that category.

    Optional: ?featured=true → only items flagged featured (uses is_published
    + first category; we don't have a featured flag on items, so this is a
    no-op for now and kept for future compatibility).

    Never exposes quantity_owned. Includes per-item wa_link.
    """
    category_slug = request.args.get("category")

    if not category_slug:
        # Landing mode — return categories with published-item counts
        cats = (
            InventoryCategory.query
            .order_by(InventoryCategory.sort_order.asc(), InventoryCategory.name.asc())
            .all()
        )
        return ok([
            {
                "slug": c.slug,
                "name": c.name,
                "short_description": c.short_description,
                "long_description": c.long_description,
                "icon": c.icon,
                "hero_image_url": None,  # not a column today; safe null
                "published_item_count": sum(1 for i in c.items if i.is_published),
            }
            for c in cats
            if any(i.is_published for i in c.items)  # hide empty categories publicly
        ])

    # Category mode
    cat = InventoryCategory.query.filter_by(slug=category_slug).first()
    if not cat:
        raise NotFoundError("Rental category not found.")

    items = (
        InventoryItem.query
        .filter(
            InventoryItem.category_id == cat.id,
            InventoryItem.is_published.is_(True),
        )
        .order_by(InventoryItem.sort_order.asc(), InventoryItem.name.asc())
        .all()
    )

    phone = get_public_whatsapp_phone()
    return ok([_dump_rental_item(i, whatsapp_phone=phone, category=cat) for i in items],
              meta={
                  "category": {
                      "slug": cat.slug,
                      "name": cat.name,
                      "short_description": cat.short_description,
                      "long_description": cat.long_description,
                      "icon": cat.icon,
                  },
                  "count": len(items),
              })





@api_v1.get("/rentals/categories")
def public_list_rental_categories():
    """
    Explicit categories endpoint (mirrors /services/categories).
    Useful for footer links and sitemap generation. Includes empty-safe counts.
    """
    cats = (
        InventoryCategory.query
        .order_by(InventoryCategory.sort_order.asc(), InventoryCategory.name.asc())
        .all()
    )
    return ok([
        {
            "slug": c.slug,
            "name": c.name,
            "short_description": c.short_description,
            "long_description": c.long_description,
            "icon": c.icon,
            "published_item_count": sum(1 for i in c.items if i.is_published),
        }
        for c in cats
    ])




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








@api_v1.get("/rentals/<category_slug>/<item_slug>")
def public_get_rental_item(category_slug, item_slug):
    """
    Detail for a single rental item. 404 if the category doesn't exist,
    the item doesn't exist in that category, or the item isn't published.
    """
    item = (
        InventoryItem.query
        .join(InventoryCategory, InventoryItem.category_id == InventoryCategory.id)
        .filter(
            InventoryCategory.slug == category_slug,
            InventoryItem.slug == item_slug,
            InventoryItem.is_published.is_(True),
        )
        .first()
    )
    if not item:
        raise NotFoundError("Rental item not found.")



    phone = get_public_whatsapp_phone()
    payload = _dump_rental_item(item, whatsapp_phone=phone)

    # Add the richer fields only on the detail view (keeps list responses light)
    payload.update({
        "long_description": item.long_description,
        "seo_title": item.seo_title,
        "seo_description": item.seo_description,
    })
    return ok(payload)








# ─── Public: Rental Hire List enquiry ───────────────────────────────

import json as _json

@api_v1.post("/enquiries/rentals")
@limiter.limit("10 per minute")
def public_submit_rental_enquiry():
    """
    Accepts a structured hire-list enquiry from the public site.

    Payload:
      items: list[{ id, slug, name, quantity, from_price, unit, currency }]
      event: { date, location, type, notes }
      contact: { name, phone, email? }

    Stored as a ContactMessage with subject='rental_hire_enquiry'.
    Never confirms a booking — owner replies manually.
    Returns { enquiry_ref } so the frontend can show a confirmation.
    """
    from app.models import ContactMessage
    from app.services import get_public_whatsapp_phone
    from datetime import datetime
    import uuid

    payload = request.get_json(silent=True) or {}

    items = payload.get("items") or []
    event = payload.get("event") or {}
    contact = payload.get("contact") or {}

    # ── validation (defensive — never trust the client) ─────────────
    if not isinstance(items, list) or not items:
        raise ValidationError("Your hire list is empty.")

    clean_items = []
    for it in items[:200]:  # hard cap
        try:
            qty = int(it.get("quantity") or 0)
        except (TypeError, ValueError):
            qty = 0
        if qty < 1:
            continue
        clean_items.append({
            "id": str(it.get("id") or ""),
            "slug": str(it.get("slug") or ""),
            "name": str(it.get("name") or "")[:200],
            "quantity": min(qty, 9999),
            "from_price": float(it.get("from_price") or 0),
            "unit": str(it.get("unit") or "")[:80],
            "currency": str(it.get("currency") or "KES")[:8],
        })

    if not clean_items:
        raise ValidationError("Your hire list is empty.")

    name = str(contact.get("name") or "").strip()
    phone = str(contact.get("phone") or "").strip()
    email = str(contact.get("email") or "").strip() or None
    if not name or not phone:
        raise ValidationError("Name and phone are required.")

    event_date = str(event.get("date") or "").strip() or None
    event_location = str(event.get("location") or "").strip() or None
    event_type = str(event.get("type") or "").strip() or None
    notes = str(event.get("notes") or "").strip() or None

    # ── build a human-readable summary (used in admin + WhatsApp) ──
    summary_lines = [
        "RENTAL HIRE ENQUIRY",
        f"Event date: {event_date or 'not specified'}",
        f"Location:   {event_location or 'not specified'}",
        f"Type:       {event_type or 'not specified'}",
        "",
        "Items requested:",
    ]
    subtotal = 0.0
    currency = clean_items[0]["currency"] if clean_items else "KES"
    for it in clean_items:
        line_total = it["from_price"] * it["quantity"]
        subtotal += line_total
        summary_lines.append(
            f"  • {it['quantity']} × {it['name']} — "
            f"{it['currency']} {it['from_price']:,.0f} / {it['unit']} "
            f"= {it['currency']} {line_total:,.0f}"
        )
    summary_lines += [
        "",
        f"Estimated subtotal: {currency} {subtotal:,.0f}",
        "(Final pricing confirmed after delivery & setup review.)",
    ]
    if notes:
        summary_lines += ["", "Notes:", notes]

    body_text = "\n".join(summary_lines)
    enquiry_ref = f"RH-{datetime.utcnow():%Y%m%d}-{uuid.uuid4().hex[:6].upper()}"

    # ── persist via existing ContactMessage model ───────────────────
    record = ContactMessage(
        subject=f"Rental hire enquiry {enquiry_ref}",
        name=name,
        email=email,
        phone=phone,
        message=body_text,
        meta=_json.dumps({
            "enquiry_ref": enquiry_ref,
            "items": clean_items,
            "event": {
                "date": event_date,
                "location": event_location,
                "type": event_type,
                "notes": notes,
            },
        }),
    )
    db.session.add(record)
    db.session.commit()

    # ── best-effort WhatsApp deep link for the "open in WhatsApp" CTA ─
    phone_digits = get_public_whatsapp_phone()
    wa_link = None
    if phone_digits:
        wa_link = build_wa_link(
            phone=phone_digits,
            message=body_text,
            source_ref=f"hire_list:{enquiry_ref}",
        )

    return ok({
        "enquiry_ref": enquiry_ref,
        "whatsapp_link": wa_link,
    })





# ─── Admin: service image upload ────────────────────────────────────

@api_v1.post("/admin/services/upload-image")
@login_required
@require_permission("service.create")
def admin_upload_service_image():

    if "file" not in request.files:
        return error(
            "validation_error",
            "No file provided.",
            details={"field": "file"},
            status=422,
        )

    f = request.files["file"]

    if not f.filename:
        return error(
            "validation_error",
            "Empty filename.",
            status=422,
        )

    try:
        image = process_and_store_image(
            file_bytes=f.read(),
            mime_type=f.mimetype or "image/jpeg",
            prefix="services",
        )

    except ValueError as exc:
        return error(
            "validation_error",
            str(exc),
            status=422,
        )

    return ok({
        "url": image["url"],
        "thumb_url": image["thumb_url"],
        "width": image["width"],
        "height": image["height"],
        "size_bytes": image["size_bytes"],
    }, status=201)


def get_category_image(category):
    # Prefer a dedicated category image.
    if category.hero_image_url:
        return category.hero_image_url

    # Otherwise use the first published service with an image.
    for service in category.services:
        if service.is_published and service.featured_image_url:
            return service.featured_image_url

    return None



# ─── Admin: package image upload ────────────────────────────────────

@api_v1.post("/admin/packages/upload-image")
@login_required
@require_permission("package.create")
def admin_upload_package_image():

    if "file" not in request.files:
        return error(
            "validation_error",
            "No file provided.",
            details={"field": "file"},
            status=422,
        )

    f = request.files["file"]

    if not f.filename:
        return error(
            "validation_error",
            "Empty filename.",
            status=422,
        )

    try:
        image = process_and_store_image(
            file_bytes=f.read(),
            mime_type=f.mimetype or "image/jpeg",
            prefix="packages",
        )

    except ValueError as exc:
        return error(
            "validation_error",
            str(exc),
            status=422,
        )

    return ok({
        "url": image["url"],
        "thumb_url": image["thumb_url"],
        "width": image["width"],
        "height": image["height"],
        "size_bytes": image["size_bytes"],
    }, status=201)




