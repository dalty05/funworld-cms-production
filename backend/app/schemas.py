# app/schemas.py
from marshmallow import Schema, fields, validate, validates, ValidationError


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)   # NO length rule on login


class UserSchema(Schema):
    id = fields.UUID(dump_only=True)
    email = fields.Email(required=True)
    phone = fields.Str(load_default=None)
    full_name = fields.Str(required=True, validate=validate.Length(min=2, max=255))
    is_active = fields.Bool(dump_only=True)
    created_at = fields.DateTime(dump_only=True)


class PermissionSchema(Schema):
    id = fields.UUID(dump_only=True)
    code = fields.Str(dump_only=True)
    description = fields.Str(dump_only=True)
    category = fields.Str(dump_only=True)


class RoleSchema(Schema):
    id = fields.UUID(dump_only=True)
    name = fields.Str(required=True)
    slug = fields.Str(required=True)
    description = fields.Str(load_default=None)
    is_system = fields.Bool(dump_only=True)
    is_protected = fields.Bool(dump_only=True)
    permissions = fields.List(fields.Nested(PermissionSchema), dump_only=True)


class RoleCreateSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    slug = fields.Str(required=True, validate=validate.Regexp(r"^[a-z0-9_-]+$"))
    description = fields.Str(load_default=None)
    permission_codes = fields.List(fields.Str(), load_default=[])


class UserCreateSchema(Schema):
    email = fields.Email(required=True)
    full_name = fields.Str(required=True, validate=validate.Length(min=2, max=255))
    phone = fields.Str(required=False, allow_none=True)
    password = fields.Str(required=True, validate=validate.Length(min=10, max=128))
    is_active = fields.Bool(load_default=True)



class TimelineEventSchema(Schema):
    id = fields.UUID(dump_only=True)
    entity_type = fields.Str(dump_only=True)
    entity_id = fields.UUID(dump_only=True)
    event_type = fields.Str(dump_only=True)
    actor_type = fields.Str(dump_only=True)
    actor_user_id = fields.UUID(dump_only=True, allow_none=True)
    summary = fields.Str(dump_only=True, allow_none=True)
    metadata = fields.Dict(dump_only=True, attribute="metadata_json", allow_none=True)
    created_at = fields.DateTime(dump_only=True)


class BlogCategorySchema(Schema):
    id = fields.UUID(dump_only=True)
    slug = fields.Str(required=True, validate=validate.Regexp(r"^[a-z0-9-]+$"))
    name = fields.Str(required=True, validate=validate.Length(min=2, max=120))
    description = fields.Str(allow_none=True)
    seo_title = fields.Str(allow_none=True)
    seo_description = fields.Str(allow_none=True)
    sort_order = fields.Int(load_default=0)


class BlogTagSchema(Schema):
    id = fields.UUID(dump_only=True)
    slug = fields.Str(required=True, validate=validate.Regexp(r"^[a-z0-9-]+$"))
    name = fields.Str(required=True, validate=validate.Length(min=2, max=120))


class BlogPostCreateSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=3, max=255))
    body_markdown = fields.Str(load_default="")
    excerpt = fields.Str(allow_none=True)
    featured_image_url = fields.Str(allow_none=True)
    featured_image_alt = fields.Str(allow_none=True)
    seo_title = fields.Str(allow_none=True)
    seo_description = fields.Str(allow_none=True)
    canonical_url = fields.Str(allow_none=True)
    og_image_url = fields.Str(allow_none=True)
    featured = fields.Bool(load_default=False)
    category_slugs = fields.List(fields.Str(), load_default=[])
    tag_slugs = fields.List(fields.Str(), load_default=[])


class BlogPostUpdateSchema(Schema):
    title = fields.Str(validate=validate.Length(min=3, max=255))
    body_markdown = fields.Str(allow_none=True)
    excerpt = fields.Str(allow_none=True)
    featured_image_url = fields.Str(allow_none=True)
    featured_image_alt = fields.Str(allow_none=True)
    seo_title = fields.Str(allow_none=True)
    seo_description = fields.Str(allow_none=True)
    canonical_url = fields.Str(allow_none=True)
    og_image_url = fields.Str(allow_none=True)
    category_slugs = fields.List(fields.Str())
    tag_slugs = fields.List(fields.Str())
    featured = fields.Bool()


class BlogPostScheduleSchema(Schema):
    scheduled_for = fields.DateTime(required=True)


class BlogPostRejectSchema(Schema):
    reason = fields.Str(required=True, validate=validate.Length(min=3, max=500))


blog_category_schema = BlogCategorySchema()
blog_categories_schema = BlogCategorySchema(many=True)
blog_tag_schema = BlogTagSchema()
blog_tags_schema = BlogTagSchema(many=True)
blog_post_create_schema = BlogPostCreateSchema()
blog_post_update_schema = BlogPostUpdateSchema()
blog_post_schedule_schema = BlogPostScheduleSchema()
blog_post_reject_schema = BlogPostRejectSchema()



class ServiceCategorySchema(Schema):
    slug = fields.Str(required=True, validate=validate.Length(max=60))
    name = fields.Str(required=True, validate=validate.Length(max=120))
    short_description = fields.Str(allow_none=True, validate=validate.Length(max=500))
    long_description = fields.Str(allow_none=True)
    hero_image_url = fields.Str(allow_none=True, validate=validate.Length(max=500))
    accent_color = fields.Str(allow_none=True, validate=validate.Length(max=20))
    sort_order = fields.Int(load_default=0)
    seo_title = fields.Str(allow_none=True, validate=validate.Length(max=255))
    seo_description = fields.Str(allow_none=True, validate=validate.Length(max=320))


service_category_schema = ServiceCategorySchema()
service_categories_schema = ServiceCategorySchema(many=True)



class ServiceCreateSchema(Schema):
    category_id = fields.UUID(required=True)
    name = fields.Str(required=True, validate=validate.Length(min=2, max=255))
    short_description = fields.Str(allow_none=True, validate=validate.Length(max=500))
    long_description = fields.Str(allow_none=True)
    featured_image_url = fields.Str(allow_none=True)
    gallery = fields.List(fields.Str(), allow_none=True)
    price_note = fields.Str(allow_none=True, validate=validate.Length(max=100))
    tags = fields.List(fields.Str(), allow_none=True)
    sort_order = fields.Int(load_default=0)
    seo_title = fields.Str(allow_none=True)
    seo_description = fields.Str(allow_none=True)


class ServiceUpdateSchema(ServiceCreateSchema):
    category_id = fields.UUID()  # optional on update


class PackageCreateSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=3, max=255))
    tagline = fields.Str(allow_none=True, validate=validate.Length(max=255))
    short_description = fields.Str(allow_none=True, validate=validate.Length(max=500))
    long_description = fields.Str(allow_none=True)
    what_is_included = fields.List(fields.Str(), allow_none=True)
    what_is_not_included = fields.List(fields.Str(), allow_none=True)
    hero_image_url = fields.Str(allow_none=True)
    gallery = fields.List(fields.Str(), allow_none=True)
    category_id = fields.UUID(allow_none=True)
    price_amount = fields.Decimal(allow_none=True, as_string=True)
    price_note = fields.Str(allow_none=True, validate=validate.Length(max=120))
    currency = fields.Str(load_default="KES", validate=validate.Length(equal=3))
    min_guests = fields.Int(allow_none=True, validate=validate.Range(min=0))
    max_guests = fields.Int(allow_none=True, validate=validate.Range(min=0))
    duration_hours = fields.Int(allow_none=True, validate=validate.Range(min=0))
    availability_note = fields.Str(allow_none=True, validate=validate.Length(max=255))
    is_featured = fields.Bool(load_default=False)
    seo_title = fields.Str(allow_none=True)
    seo_description = fields.Str(allow_none=True)


class PackageUpdateSchema(PackageCreateSchema):
    name = fields.Str(validate=validate.Length(min=3, max=255))


class PackageRejectSchema(Schema):
    reason = fields.Str(required=True, validate=validate.Length(min=3, max=500))


service_create_schema = ServiceCreateSchema()
service_update_schema = ServiceUpdateSchema()
package_create_schema = PackageCreateSchema()
package_update_schema = PackageUpdateSchema()
package_reject_schema = PackageRejectSchema()






class InventoryCategorySchema(Schema):
    slug = fields.Str(required=True, validate=validate.Length(min=2, max=80))
    name = fields.Str(required=True, validate=validate.Length(min=2, max=120))
    short_description = fields.Str(allow_none=True, validate=validate.Length(max=500))
    long_description = fields.Str(allow_none=True)
    icon = fields.Str(allow_none=True)
    sort_order = fields.Int(load_default=0)
    seo_title = fields.Str(allow_none=True)
    seo_description = fields.Str(allow_none=True)


class InventoryItemCreateSchema(Schema):
    category_id = fields.UUID(required=True)
    name = fields.Str(required=True, validate=validate.Length(min=2, max=255))
    short_description = fields.Str(allow_none=True, validate=validate.Length(max=500))
    long_description = fields.Str(allow_none=True)
    quantity_owned = fields.Int(load_default=0, validate=validate.Range(min=0))
    quantity_available_note = fields.Str(allow_none=True, validate=validate.Length(max=255))
    unit_price_hint = fields.Decimal(allow_none=True, as_string=True)
    unit = fields.Str(allow_none=True, validate=validate.Length(max=40))
    currency = fields.Str(load_default="KES", validate=validate.Length(equal=3))
    featured_image_url = fields.Str(allow_none=True)
    gallery = fields.List(fields.Str(), allow_none=True)
    tags = fields.List(fields.Str(), allow_none=True)
    sort_order = fields.Int(load_default=0)
    seo_title = fields.Str(allow_none=True)
    seo_description = fields.Str(allow_none=True)


class InventoryItemUpdateSchema(InventoryItemCreateSchema):
    category_id = fields.UUID()


class InventoryLinkSchema(Schema):
    inventory_item_id = fields.UUID(required=True)
    quantity = fields.Int(load_default=1, validate=validate.Range(min=1))
    notes = fields.Str(allow_none=True, validate=validate.Length(max=255))
    sort_order = fields.Int(load_default=0)


class InventoryLinksReplaceSchema(Schema):
    items = fields.List(fields.Nested(InventoryLinkSchema), required=True)


inventory_category_schema = InventoryCategorySchema()
inventory_item_create_schema = InventoryItemCreateSchema()
inventory_item_update_schema = InventoryItemUpdateSchema()
inventory_links_replace_schema = InventoryLinksReplaceSchema()







class SettingUpdateSchema(Schema):
    value_text = fields.Str(allow_none=True)
    label = fields.Str(allow_none=True, validate=validate.Length(max=255))
    is_published = fields.Bool(allow_none=True)


class SettingCreateSchema(Schema):
    key = fields.Str(required=True, validate=validate.Length(min=2, max=80))
    label = fields.Str(required=True, validate=validate.Length(max=255))
    category = fields.Str(required=True, validate=validate.OneOf(
        ["policy", "company", "quote_terms", "invoice_terms"]
    ))
    value_text = fields.Str(allow_none=True)
    description = fields.Str(allow_none=True)


setting_update_schema = SettingUpdateSchema()
setting_create_schema = SettingCreateSchema()





