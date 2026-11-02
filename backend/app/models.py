# models.py
import enum
import uuid
from datetime import datetime, date, timezone

from sqlalchemy import (
    Boolean, Date, Column,DateTime, Enum, ForeignKey, Integer, Numeric, String, Table, Text, TypeDecorator, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

# from app.extensions import db

from app import db

def utcnow() -> datetime:
    return datetime.now(timezone.utc)



class UUIDMixin:
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

class CompatibleEnum(TypeDecorator):
    impl = String
    cache_ok = True

    def __init__(self, enum_class, length, aliases=()):
        self.enum_class = enum_class
        self.aliases = tuple(aliases)
        super().__init__(length=length)

    def _normalize(self, value):
        if value is None:
            return None
        normalized = value.value if isinstance(value, self.enum_class) else str(value)
        normalized = normalized.strip().lower().replace(" ", "_")
        normalized = dict(self.aliases).get(normalized, normalized)
        return self.enum_class(normalized).value

    def process_bind_param(self, value, dialect):
        return self._normalize(value)

    def process_result_value(self, value, dialect):
        normalized = self._normalize(value)
        return self.enum_class(normalized) if normalized is not None else None




class TimelineEvent(db.Model, UUIDMixin, TimestampMixin):
    __tablename__ = "timeline_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    __table_args__ = (
        db.Index("ix_timeline_events_created_at", "created_at"),
        db.Index("ix_timeline_events_entity_id", "entity_id"),
        db.Index("ix_timeline_events_entity_type", "entity_type"),
        db.Index("ix_timeline_events_event_type", "event_type"),

        # Phase 8 indexes
        db.Index( "ix_timeline_entity_created", "entity_type", "entity_id", "created_at", ),
        db.Index( "ix_timeline_actor_created", "actor_user_id", "created_at", ),
        db.Index( "ix_timeline_event_created", "event_type", "created_at", ),


    )

    entity_type: Mapped[str] = mapped_column( String(50), nullable=False, )

    entity_id: Mapped[uuid.UUID] = mapped_column( UUID(as_uuid=True), nullable=False, )

    event_type: Mapped[str] = mapped_column( String(80), nullable=False, )
    
    actor_type: Mapped[str] = mapped_column(String(20), default="user", nullable=False)  # user | customer | system
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    summary: Mapped[str | None] = mapped_column(String(500), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)


    def __repr__(self):
        return f"<TimelineEvent {self.entity_type}:{self.entity_id} {self.event_type}>"

    # @classmethod
    # def append(cls, **kwargs):
    #     from app.services import record_event
    #     return record_event(**kwargs)



class TimelineEventType(str, enum.Enum):

    # ── Auth / RBAC (audit-only, not usually on entity timelines) ───
    AUTH_LOGIN                  = "auth.login"
    AUTH_LOGOUT                 = "auth.logout"
    AUTH_FAILED                 = "auth.failed"
    ROLE_CREATED                = "role.created"
    ROLE_UPDATED                = "role.updated"
    ROLE_DELETED                = "role.deleted"
    ROLE_ASSIGNED               = "role.assigned"
    ROLE_REVOKED                = "role.revoked"
    USER_CREATED                = "user.created"
    USER_UPDATED                = "user.updated"
    USER_DEACTIVATED            = "user.deactivated"


    # ── Services lifecycle ──────────────────────────────────────────
    SERVICE_CREATED    = "service.created"
    SERVICE_UPDATED    = "service.updated"
    SERVICE_PUBLISHED  = "service.published"
    SERVICE_UNPUBLISHED = "service.unpublished"
    SERVICE_DELETED    = "service.deleted"

    
    # ── Inventory item lifecycle ────────────────────────────────────
    INVENTORY_ITEM_CREATED      = "inventory_item.created"
    INVENTORY_ITEM_UPDATED      = "inventory_item.updated"
    INVENTORY_ITEM_PUBLISHED    = "inventory_item.published"
    INVENTORY_ITEM_UNPUBLISHED  = "inventory_item.unpublished"
    INVENTORY_ITEM_DELETED      = "inventory_item.deleted"




    # ── Inventory item lifecycle ────────────────────────────────────
    PACKAGE_APPROVED            = "package.approved"
    PACKAGE_REJECTED            = "package.rejected"
    PACKAGE_PUBLISHED           = "package.published"
    PACKAGE_SUBMITTED           = "package.submitted"
    PACKAGE_CREATED             = "package.created"
    GALLERY_IMAGE_PUBLISHED     = "gallery_image.published"

    # ── Blog post lifecycle ─────────────────────────────────────────
    BLOG_POST_CREATED    = "blog_post.created"
    BLOG_POST_UPDATED    = "blog_post.updated"
    BLOG_POST_SUBMITTED  = "blog_post.submitted"
    BLOG_POST_APPROVED   = "blog_post.approved"
    BLOG_POST_REJECTED   = "blog_post.rejected"
    BLOG_POST_PUBLISHED  = "blog_post.published"
    BLOG_POST_ARCHIVED   = "blog_post.archived"

    






    
# ─── Auth / RBAC ────────────────────────────────────────────────

role_permissions = Table(
    "role_permissions",
    db.metadata,
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)



class User(db.Model, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    token_version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    role_assignments = relationship("RoleAssignment", back_populates="user", cascade="all, delete-orphan", foreign_keys="RoleAssignment.user_id")


    def has_permission(self, code, scope_type=None, scope_id=None):
        for a in self.role_assignments:
            if not a.is_active:
                continue
            if scope_type and a.scope_type != scope_type:
                continue
            if scope_id and str(a.scope_id) != str(scope_id):
                continue

            # Exact match
            if a.role.has_permission(code):
                return True

          
            base = code.rsplit(".", 1)[0] if "." in code else None
            if base and base != code:
                for suffix in (".all", ".own"):
                    if a.role.has_permission(base + suffix):
                        return True

        return False


class RevokedToken(db.Model):
    __tablename__ = "revoked_tokens"

    jti: Mapped[str] = mapped_column(String(36), primary_key=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True,
    )
    revoked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False,
    )


class Permission(db.Model, UUIDMixin, TimestampMixin):
    __tablename__ = "permissions"

    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)


class Role(db.Model, UUIDMixin, TimestampMixin):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_protected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    permissions = relationship("Permission", secondary=role_permissions, lazy="selectin")
    assignments = relationship("RoleAssignment", back_populates="role", cascade="all, delete-orphan")

    def has_permission(self, code: str) -> bool:
        return any(p.code == code for p in self.permissions)


class RoleAssignment(db.Model, UUIDMixin, TimestampMixin):
    __tablename__ = "role_assignments"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scope_type: Mapped[str] = mapped_column(String(20), default="global", nullable=False)
    scope_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    granted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    granted_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    user = relationship("User", back_populates="role_assignments", foreign_keys=[user_id])

    granted_by = relationship(
        "User",
        foreign_keys=[granted_by_user_id],
    )



    role = relationship("Role", back_populates="assignments")



class AuditLog(db.Model, UUIDMixin, TimestampMixin):
    __tablename__ = "audit_logs"

    __table_args__ = (
    # Existing Phase 1 indexes — preserve them
        db.Index("ix_audit_logs_action", "action"),
        db.Index("ix_audit_logs_actor_user_id", "actor_user_id"),
        db.Index("ix_audit_logs_entity_id", "entity_id"),
        db.Index("ix_audit_logs_entity_type", "entity_type"),
        db.Index("ix_audit_logs_request_id", "request_id"),

        # Phase 8 indexes
        db.Index( "ix_audit_entity_created", "entity_type", "entity_id", "created_at", ),
        db.Index( "ix_audit_actor_created", "actor_user_id", "created_at", ),
        db.Index( "ix_audit_action_created", "action", "created_at", ),
        db.Index( "ix_audit_created", "created_at", ),

        )

    actor_user_id: Mapped[uuid.UUID | None] = mapped_column( UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, )
    actor_type: Mapped[str] = mapped_column( String(20), default="user", nullable=False, )
    action: Mapped[str] = mapped_column( String(100), nullable=False, )
    entity_type: Mapped[str | None] = mapped_column( String(50), nullable=True, )
    entity_id: Mapped[str | None] = mapped_column( String(100), nullable=True, )
    before: Mapped[dict | None] = mapped_column( JSONB, nullable=True, )
    after: Mapped[dict | None] = mapped_column( JSONB, nullable=True, )
    ip_address: Mapped[str | None] = mapped_column( String(45), nullable=True, )
    user_agent: Mapped[str | None] = mapped_column( Text, nullable=True, )
    request_id: Mapped[str | None] = mapped_column( String(64), nullable=True, )
    # Phase 8 integrity fields
    before_hash: Mapped[str | None] = mapped_column( String(64), nullable=True, )
    after_hash: Mapped[str | None] = mapped_column( String(64), nullable=True, )
    prev_hash: Mapped[str | None] = mapped_column( String(64), nullable=True, index=True, )
    row_hash: Mapped[str | None] = mapped_column( String(64), nullable=True, index=True, )


class IdempotencyKey(db.Model, UUIDMixin, TimestampMixin):
    __tablename__ = "idempotency_keys"
    __table_args__ = (UniqueConstraint("scope", "key", name="uq_idempotency_scope_key"),)

    key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    scope: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="processing", nullable=False, index=True)
    response_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_body: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


class ContactMessage(db.Model, UUIDMixin, TimestampMixin):
    __tablename__ = "contact_messages"

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    handled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    handled_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True,
    )

# ─── Phase 12: Blog & Content ───────────────────────────────────────

class BlogPostStatus(str, enum.Enum):
    DRAFT     = "draft"
    REVIEW    = "review"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    ARCHIVED  = "archived"
    REJECTED  = "rejected"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            normalized = value.strip().lower().replace(" ", "_")
            if normalized in cls._value2member_map_:
                return cls(normalized)
        return None


class BlogCategory(db.Model, UUIDMixin, TimestampMixin):
    __tablename__ = "blog_categories"

    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # SEO
    seo_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    seo_description: Mapped[str | None] = mapped_column(String(320), nullable=True)

    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    def __repr__(self):
        return f"<BlogCategory {self.slug}>"


class BlogTag(db.Model, UUIDMixin, TimestampMixin):
    __tablename__ = "blog_tags"

    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)

    def __repr__(self):
        return f"<BlogTag {self.slug}>"


# Association tables
blog_post_categories = Table(
    "blog_post_categories",
    db.metadata,
    Column("post_id", UUID(as_uuid=True),
           ForeignKey("blog_posts.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", UUID(as_uuid=True),
           ForeignKey("blog_categories.id", ondelete="CASCADE"), primary_key=True),
)

blog_post_tags = Table(
    "blog_post_tags",
    db.metadata,
    Column("post_id", UUID(as_uuid=True),
           ForeignKey("blog_posts.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", UUID(as_uuid=True),
           ForeignKey("blog_tags.id", ondelete="CASCADE"), primary_key=True),
)


class BlogPost(db.Model, UUIDMixin, TimestampMixin):
    __tablename__ = "blog_posts"
    __table_args__ = (
        db.Index("ix_blog_status_published",
                 "status", "published_at"),
    )

    # Identity
    slug: Mapped[str] = mapped_column(String(160), unique=True,
                                      nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    excerpt: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Content — Markdown preferred, HTML accepted
    body_markdown: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Rendered on save from markdown → html. Never trust HTML from the client directly.

    # Media
    featured_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    featured_image_alt: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Author / workflow
    author_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True,
    )
    status: Mapped[BlogPostStatus] = mapped_column(
        Enum(BlogPostStatus, name="blog_post_status",
             native_enum=False, length=20,
             values_callable=lambda x: [e.value for e in x]),
        default=BlogPostStatus.DRAFT, nullable=False, index=True,
    )

    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True,
    )
    scheduled_for: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True,
    )
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    # SEO
    seo_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    seo_description: Mapped[str | None] = mapped_column(String(320), nullable=True)
    canonical_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    og_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Reading meta
    reading_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Editorial
    featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Workflow
    submitted_for_review_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    reviewed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    author = relationship("User", foreign_keys=[author_user_id])
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_user_id])
    categories = relationship(
        "BlogCategory", secondary=blog_post_categories, lazy="selectin",
        order_by="BlogCategory.sort_order",
    )
    tags = relationship("BlogTag", secondary=blog_post_tags, lazy="selectin")

    def __repr__(self):
        return f"<BlogPost {self.slug} [{self.status.value}]>"


class BlogPostRevision(db.Model, UUIDMixin):
    """Immutable snapshot of a post body each time it's saved.
    Lets you roll back and see who changed what."""
    __tablename__ = "blog_post_revisions"

    post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("blog_posts.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body_markdown: Mapped[str | None] = mapped_column(Text, nullable=True)
    saved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False, index=True,
    )

    def __repr__(self):
        return f"<BlogPostRevision {self.post_id} v{self.revision_number}>"


    
# ─── Phase 18: Services & Packages ──────────────────────────────────

class ServiceCategoryType(str, enum.Enum):
    WEDDINGS  = "weddings"
    KIDS      = "kids"
    CORPORATE = "corporate"
    FUNDAYS   = "fundays"


class ServiceCategory(db.Model, UUIDMixin, TimestampMixin):
    """
    Fixed set of four. Seeded once, editable but not creatable by admin.
    """
    __tablename__ = "service_categories"

    slug: Mapped[str] = mapped_column(String(60), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    short_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    long_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    hero_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    accent_color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # SEO
    seo_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    seo_description: Mapped[str | None] = mapped_column(String(320), nullable=True)

    services = relationship(
        "Service",
        back_populates="category",
        cascade="all, delete-orphan",
        order_by="Service.sort_order",
    )

    def __repr__(self):
        return f"<ServiceCategory {self.slug}>"


class Service(db.Model, UUIDMixin, TimestampMixin):
    """
    One offering. Not priced publicly — the customer requests a quote.
    """
    __tablename__ = "services"
    __table_args__ = (
        UniqueConstraint("category_id", "slug", name="uq_service_category_slug"),
    )

    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("service_categories.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    slug: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    short_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    long_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    featured_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    gallery: Mapped[list | None] = mapped_column(JSONB, nullable=True)   # ["url1","url2"]

    price_note: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # Free text like "From KES 5,000/day" — informational only. The quote is
    # always generated by hand.

    tags: Mapped[list | None] = mapped_column(JSONB, nullable=True)   # ["outdoor","rental"]

    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # SEO
    seo_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    seo_description: Mapped[str | None] = mapped_column(String(320), nullable=True)

    category = relationship("ServiceCategory", back_populates="services")

    def __repr__(self):
        return f"<Service {self.slug} [{'published' if self.is_published else 'draft'}]>"


class PackageStatus(str, enum.Enum):
    DRAFT          = "draft"
    PENDING_REVIEW = "pending_review"
    PUBLISHED      = "published"
    REJECTED       = "rejected"
    ARCHIVED       = "archived"


class Package(db.Model, UUIDMixin, TimestampMixin):
    """
    A hosted event the company sells as a bundle, with a fixed price.

    Unlike a Service (which is a "we do this, ask us for a quote"),
    a Package is a specific event: date, venue, price, capacity.
    The public can book directly.
    """
    __tablename__ = "packages"

    slug: Mapped[str] = mapped_column(String(140), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    tagline: Mapped[str | None] = mapped_column(String(255), nullable=True)

    short_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    long_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    what_is_included: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # ["Décor","Catering","MC"]
    what_is_not_included: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    hero_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    gallery: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Category link (optional — a package can be tied to Weddings, Kids, etc.)
    category_id: Mapped[uuid.UUID | None] = mapped_column( UUID(as_uuid=True), ForeignKey("service_categories.id", ondelete="SET NULL"), nullable=True, index=True, )

    # Pricing — display only; the customer always goes through an enquiry
    price_amount: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    price_note: Mapped[str | None] = mapped_column(String(120), nullable=True)
    # "From", "per person", "for 50 guests"
    currency: Mapped[str] = mapped_column(String(3), default="KES", nullable=False)

    # Capacity and logistics
    min_guests: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_guests: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Availability — free text for now; not enforced by the system
    availability_note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # "Available year-round", "Book 4 weeks in advance", etc.

    # Workflow
    status: Mapped[PackageStatus] = mapped_column( Enum(PackageStatus, name="package_status", native_enum=False, length=20, values_callable=lambda x: [e.value for e in x]), default=PackageStatus.DRAFT, nullable=False, index=True, )

    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column( UUID(as_uuid=True), ForeignKey("users.id"), nullable=True,)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by_user_id: Mapped[uuid.UUID | None] = mapped_column( UUID(as_uuid=True), ForeignKey("users.id"), nullable=True,)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Marketing
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # SEO
    seo_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    seo_description: Mapped[str | None] = mapped_column(String(320), nullable=True)

    # Relationships
    category = relationship("ServiceCategory")
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_user_id])
    services = relationship( "Service", secondary="package_services", lazy="selectin", )
    inventory_items = relationship( "PackageInventoryItem", back_populates="package", cascade="all, delete-orphan", order_by="PackageInventoryItem.sort_order", )





    def __repr__(self):
        return f"<Package {self.slug} [{self.status.value}]>"


# Package ↔ Service many-to-many
package_services = Table(
    "package_services",
    db.metadata,
    Column("package_id", UUID(as_uuid=True),
           ForeignKey("packages.id", ondelete="CASCADE"), primary_key=True),
    Column("service_id", UUID(as_uuid=True),
           ForeignKey("services.id", ondelete="CASCADE"), primary_key=True),
)

# ─── Phase 19: Inventory ────────────────────────────────────────────

class InventoryCategory(db.Model, UUIDMixin, TimestampMixin):
    """
    Grouping for physical items the company owns.
    e.g. "Tents & Seating", "Catering Equipment", "Sound & Lighting"
    """
    __tablename__ = "inventory_categories"

    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    short_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    long_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    seo_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    seo_description: Mapped[str | None] = mapped_column(String(320), nullable=True)

    items = relationship(
        "InventoryItem",
        back_populates="category",
        cascade="all, delete-orphan",
        order_by="InventoryItem.sort_order",
    )

    def __repr__(self):
        return f"<InventoryCategory {self.slug}>"


class InventoryItem(db.Model, UUIDMixin, TimestampMixin):
    """
    A physical item the company owns and can rent/hire out.
    NOT a service — services are things we DO. This is things we HAVE.
    """
    __tablename__ = "inventory_items"
    __table_args__ = (
        UniqueConstraint("category_id", "slug", name="uq_inventory_category_slug"),
    )

    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inventory_categories.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    slug: Mapped[str] = mapped_column(String(140), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    short_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    long_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Inventory
    quantity_owned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quantity_available_note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # "Some units under maintenance", "Includes 2 spare legs per table"

    # Pricing hint (informational — the quote is still authored by hand)
    unit_price_hint: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(40), nullable=True)
    # "per piece", "per day", "per event", "per 100 pieces"
    currency: Mapped[str] = mapped_column(String(3), default="KES", nullable=False)

    # Media
    featured_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    gallery: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    tags: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    seo_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    seo_description: Mapped[str | None] = mapped_column(String(320), nullable=True)

    category = relationship("InventoryCategory", back_populates="items")

    def __repr__(self):
        return f"<InventoryItem {self.slug} qty={self.quantity_owned}>"


# ─── Package ↔ Inventory (with quantity) ────────────────────────────

class PackageInventoryItem(db.Model, UUIDMixin):
    """
    Which inventory items a package includes, and how many.
    """
    __tablename__ = "package_inventory_items"
    __table_args__ = (
        UniqueConstraint("package_id", "inventory_item_id",
                         name="uq_package_inventory_item"),
    )

    package_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("packages.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    inventory_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inventory_items.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    package = relationship("Package")
    inventory_item = relationship("InventoryItem")

    def __repr__(self):
        return f"<PackageInventoryItem pkg={self.package_id} item={self.inventory_item_id} qty={self.quantity}>"



# ─── Gallery ────────────────────────────────────────────────────────

class GalleryAlbum(db.Model, UUIDMixin, TimestampMixin):
    """
    Optional grouping — e.g. "Molly & Brian's Wedding", "2024 Fundays".
    If you don't want albums, images can exist without one.
    """
    __tablename__ = "gallery_albums"

    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Optional link to a service category (Weddings, Kids, etc.)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("service_categories.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )

    cover_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    seo_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    seo_description: Mapped[str | None] = mapped_column(String(320), nullable=True)

    category = relationship("ServiceCategory")
    images = relationship(
        "GalleryImage",
        back_populates="album",
        cascade="all, delete-orphan",
        order_by="GalleryImage.sort_order",
    )

    def __repr__(self):
        return f"<GalleryAlbum {self.slug}>"


class GalleryImage(db.Model, UUIDMixin, TimestampMixin):
    """
    A single photo in the gallery. Can belong to an album or stand alone.
    """
    __tablename__ = "gallery_images"

    album_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("gallery_albums.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )

    # Direct link to a category if not in an album
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("service_categories.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )

    # Storage
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    # e.g. "gallery/2026/a1b2c3d4.jpg"
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    # Public URL or path (usually "/api/v1/gallery/files/<key>" for local storage)

    # Metadata
    caption: Mapped[str | None] = mapped_column(String(500), nullable=True)
    alt_text: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    # Required for accessibility. Empty string is allowed but discouraged.

    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(40), nullable=True)

    # Organisation
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Provenance
    uploaded_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True,
    )

    album = relationship("GalleryAlbum", back_populates="images")
    category = relationship("ServiceCategory")
    uploaded_by = relationship("User", foreign_keys=[uploaded_by_user_id])

    def __repr__(self):
        return f"<GalleryImage {self.id} {'published' if self.is_published else 'draft'}>"









# ─── Phase 21: Settings ─────────────────────────────────────────────

class SettingCategory(str, enum.Enum):
    POLICY         = "policy"           # privacy, terms, refund, cancellation
    COMPANY        = "company"          # name, address, phone, KRA PIN
    QUOTE_TERMS    = "quote_terms"      # default terms on new quotes
    PAYMENT_TERMS  = "payment_terms"    # default terms on new invoices


class Setting(db.Model, UUIDMixin, TimestampMixin):
    """
    Key-value store for editable text/config.
    Versioned: each save bumps `version` and stores the previous value in
    `SettingRevision` for undo.
    """
    __tablename__ = "settings"
    __table_args__ = (
        UniqueConstraint("key", name="uq_settings_key"),
    )

    key: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    # "privacy_policy", "terms_of_service", "refund_policy",
    # "quote_default_terms", "invoice_default_terms",
    # "company_name", "company_address", ...

    category: Mapped[SettingCategory] = mapped_column(
        Enum(SettingCategory, name="setting_category",
             native_enum=False, length=30,
             values_callable=lambda x: [e.value for e in x]),
        default=SettingCategory.POLICY, nullable=False, index=True,
    )

    label: Mapped[str] = mapped_column(String(255), nullable=False)
    # Human-readable: "Privacy Policy"

    value_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    # For policies: markdown/HTML body.
    # For company fields: the value.
    # For quote/invoice terms: default text shown in the PDF.

    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Help text shown in the admin form.

    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # System settings can't be deleted (only edited).

    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    updated_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True,
    )

    def __repr__(self):
        return f"<Setting {self.key}>"


class SettingRevision(db.Model, UUIDMixin):
    """Immutable snapshot of every change to a setting."""
    __tablename__ = "setting_revisions"

    setting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("settings.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    value_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False, index=True,
    )

    def __repr__(self):
        return f"<SettingRevision {self.setting_id} v{self.version}>"



# ─── Phase 21: Analytics ────────────────────────────────────────────

class VisitorSession(db.Model, UUIDMixin):
    """One per browsing session. Rotated every 30 minutes of inactivity."""
    __tablename__ = "visitor_sessions"

    session_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    ip_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    country: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    region: Mapped[str | None] = mapped_column(String(64), nullable=True)
    city: Mapped[str | None] = mapped_column(String(64), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    isp: Mapped[str | None] = mapped_column(String(128), nullable=True)

    referrer: Mapped[str | None] = mapped_column(String(500), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )

    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False, index=True,
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False, index=True,
    )
    page_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)



    def __repr__(self):
        return f"<VisitorSession {self.session_id[:8]}… {self.country}>"


class PageView(db.Model, UUIDMixin):
    __tablename__ = "page_views"
    __table_args__ = (
        db.Index("ix_pageview_path_created", "path", "created_at"),
        db.Index("ix_pageview_session", "session_id", "created_at"),
    )

    session_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    path: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    referrer: Mapped[str | None] = mapped_column(String(500), nullable=True)

    country: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    city: Mapped[str | None] = mapped_column(String(64), nullable=True)

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False, index=True,
    )

    def __repr__(self):
        return f"<PageView {self.path} @ {self.created_at}>"



