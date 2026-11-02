# seeds.py
from app import db
from app.models import Permission, Role

PERMISSIONS = [
    # ── Users ───────────────────────────────────────────────────────
    ("user.view",             "user",         "View users"),
    ("user.invite",           "user",         "Invite users"),
    ("user.edit",             "user",         "Edit users"),
    ("user.deactivate",       "user",         "Deactivate users"),

    # ── Roles ───────────────────────────────────────────────────────
    ("role.view",             "role",         "View roles"),
    ("role.create",           "role",         "Create roles"),
    ("role.edit",             "role",         "Edit roles"),
    ("role.edit.protected",   "role",         "Edit protected roles"),
    ("role.delete",           "role",         "Delete roles"),
    ("role.assign",           "role",         "Assign roles to users"),




    # ── Content ─────────────────────────────────────────────────────
    ("content.view",          "content",      "View content"),
    ("content.create",        "content",      "Create content"),
    ("content.edit",          "content",      "Edit content"),
    ("content.publish",       "content",      "Publish content"),

    # ── Settings ────────────────────────────────────────────────────
    ("settings.view",         "settings",     "View settings"),
    ("settings.edit",         "settings",     "Edit settings"),

    # ── Alerts & audit ──────────────────────────────────────────────
    ("alert.admin",           "alert",        "Receive admin alerts"),
    ("audit.view",            "audit",        "View audit logs and timeline"),




        # Services
    ("service.view",       "service", "View services"),
    ("service.create",     "service", "Create services"),
    ("service.edit",       "service", "Edit services"),
    ("service.publish",    "service", "Publish/unpublish services"),
    ("service.delete",     "service", "Delete services"),

    # Packages
    ("package.view",       "package", "View packages"),
    ("package.create",     "package", "Create packages"),
    ("package.edit",       "package", "Edit packages"),
    ("package.submit",     "package", "Submit packages for review"),
    ("package.approve",    "package", "Approve/reject packages"),   # Owner only
    ("package.publish",    "package", "Publish/unpublish packages"),
    ("package.delete",     "package", "Delete packages"),

        # Inventory
    ("inventory.view",      "inventory", "View inventory"),
    ("inventory.create",    "inventory", "Create inventory items"),
    ("inventory.edit",      "inventory", "Edit inventory items"),
    ("inventory.publish",   "inventory", "Publish/unpublish inventory items"),
    ("inventory.delete",    "inventory", "Delete inventory items"),



        # Gallery
    ("gallery.view",     "gallery", "View gallery"),
    ("gallery.create",   "gallery", "Upload gallery images and create albums"),
    ("gallery.edit",     "gallery", "Edit gallery metadata"),
    ("gallery.publish",  "gallery", "Publish/unpublish gallery content"),
    ("gallery.delete",   "gallery", "Delete gallery images and albums"),









]


DEFAULT_ROLES = {
    "owner": {
        "name": "Owner",
        "description": "Full access, protected role",
        "is_system": True,
        "is_protected": True,
        "permissions": "*",
    },
    "admin": {
        "name": "Administrator",
        "description": "Everything except protected-role editing",
        "is_system": True,
        "is_protected": False,
        "permissions": [p[0] for p in PERMISSIONS if p[0] != "role.edit.protected" and p[0] != "package.approve.protected" ],
    },
    "content_editor": {
        "name": "Content Editor",
        "description": "Blog, gallery, packages — no sales data",
        "is_system": True,
        "is_protected": False,
        "permissions": [
            "content.view", "content.create", "content.edit", "content.publish",
            "service.view", "service.create", "service.edit", "service.publish",
            
            "inventory.view", "inventory.create", "inventory.edit", "inventory.publish",
            "gallery.view", "gallery.create", "gallery.edit", "gallery.publish", "gallery.delete"
        ],
    },
    "viewer": {
        "name": "Viewer",
        "description": "Read-only across assigned scope",
        "is_system": True,
        "is_protected": False,
        "permissions": [
           
            "service.view", "package.view", "inventory.view","gallery.view",
        ],
    },
}


def seed_permissions_and_roles():
    # ── Permissions ─────────────────────────────────────────────────
    existing = {p.code for p in Permission.query.all()}
    for code, category, desc in PERMISSIONS:
        if code not in existing:
            db.session.add(Permission(code=code, category=category, description=desc))
            existing.add(code)          # ← IMPORTANT: mutate the set so dupes in the list are caught
    db.session.commit()

    all_perms = {p.code: p for p in Permission.query.all()}

    # ── Roles ───────────────────────────────────────────────────────
    for slug, spec in DEFAULT_ROLES.items():
        role = Role.query.filter_by(slug=slug).first()
        if not role:
            role = Role(
                slug=slug,
                name=spec["name"],
                description=spec.get("description"),
                is_system=spec.get("is_system", True),
                is_protected=spec.get("is_protected", False),
            )
            db.session.add(role)
            db.session.commit()

        if spec["permissions"] == "*":
            perms = list(all_perms.values())
        else:
            missing = [c for c in spec["permissions"] if c not in all_perms]
            if missing:
                print(f"WARNING: role '{slug}' references unknown permissions: {missing}")
            perms = [all_perms[c] for c in spec["permissions"] if c in all_perms]

        role.permissions = perms
        db.session.commit()

    print("Seeded permissions and default roles.")


from app.models import BlogCategory, BlogTag


DEFAULT_BLOG_CATEGORIES = [
    ("kids-parties",          "Kids Parties",           "Ideas, themes, and pricing for children's celebrations.", 10),
    ("school-fundays",        "School Fundays",         "Planning guides for sports days and family fun events.", 20),
    ("weddings",              "Weddings & Receptions",  "Real weddings, planning tips, and décor inspiration.", 30),
    ("corporate-events",      "Corporate Events",       "Conferences, launches, and end-of-year parties.", 40),
    ("event-decor-tips",      "Event Décor Tips",       "Design ideas, palette guidance, and setup advice.", 50),
    ("rental-guides",         "Rental Guides",          "Tents, sound, and equipment — what to hire and why.", 60),
    ("venue-planning",        "Venue & Planning",       "Choosing venues, timelines, and coordination.", 70),
    ("behind-the-scenes",     "Behind the Scenes",      "How we plan, build, and deliver events.", 80),
]


def seed_blog_categories():
    for slug, name, description, order in DEFAULT_BLOG_CATEGORIES:
        if BlogCategory.query.filter_by(slug=slug).first():
            continue
        db.session.add(BlogCategory(
            slug=slug, name=name, description=description, sort_order=order,
        ))
    db.session.commit()
    print("Seeded blog categories.")


DEFAULT_BLOG_TAGS = [
    ("nairobi", "Nairobi"),
    ("budget", "Budget"),
    ("diy", "DIY"),
    ("packages", "Packages"),
    ("kids", "Kids"),
    ("fundays", "Fundays"),
    ("weddings", "Weddings"),
    ("corporate", "Corporate"),
    ("decor", "Décor"),
]


def seed_blog_tags():
    for slug, name in DEFAULT_BLOG_TAGS:
        if BlogTag.query.filter_by(slug=slug).first():
            continue
        db.session.add(BlogTag(slug=slug, name=name))
    db.session.commit()
    print("Seeded blog tags.")






from app.models import ServiceCategory


DEFAULT_SERVICE_CATEGORIES = [
    {
        "slug": "weddings",
        "name": "Weddings & Special Occasions",
        "short_description": "Weddings, ruracio, engagements, proposals, anniversaries.",
        "long_description": "Full planning, décor, coordination, and vendor management for the day you'll never forget.",
        "accent_color": "#C9A45C",
        "sort_order": 10,
    },
    {
        "slug": "kids",
        "name": "Kids' Parties & Entertainment",
        "short_description": "Birthdays, baby showers, gender reveals, entertainment, and activities.",
        "long_description": "Themed celebrations with décor, entertainment, and everything planned end-to-end.",
        "accent_color": "#E8836B",
        "sort_order": 20,
    },


    
    {
        "slug": "corporate",
        "name": "Corporate Events",
        "short_description": "Launches, activations, conferences, team-building, and customer service week.",
        "long_description": "Conferences, product launches, brand activations — delivered with precision.",
        "accent_color": "#8FAE8A",
        "sort_order": 30,
    },
    {
        "slug": "fundays",
        "name": "School Fundays & Graduations",
        "short_description": "Mega fun days, sports days, prize-givings, and graduations.",
        "long_description": "Sports days, family fun days, and school carnivals that keep everyone moving.",
        "accent_color": "#C9A45C",
        "sort_order": 40,
    },
]


def seed_service_categories():
    for spec in DEFAULT_SERVICE_CATEGORIES:
        if ServiceCategory.query.filter_by(slug=spec["slug"]).first():
            continue
        db.session.add(ServiceCategory(**spec))
    db.session.commit()
    print("Seeded service categories.")


from app.models import InventoryCategory


# append to seeds.py
DEFAULT_INVENTORY_CATEGORIES = [
    {
        "slug": "tents-seating",
        "name": "Tents & Seating",
        "short_description": "Marquees, tents, tables, chairs, thrones.",
        "sort_order": 10,
    },
    {
        "slug": "catering-equipment",
        "name": "Catering Equipment",
        "short_description": "Chafing dishes, buffet, tableware, cake stands.",
        "sort_order": 20,
    },
    {
        "slug": "sound-lighting",
        "name": "Sound & Lighting",
        "short_description": "PA systems, microphones, event lighting.",
        "sort_order": 30,
    },
    {
        "slug": "decor-props",
        "name": "Décor & Props",
        "short_description": "Backdrops, balloons, signage, centerpieces.",
        "sort_order": 40,
    },
    {
        "slug": "kids-entertainment",
        "name": "Kids & Entertainment",
        "short_description": "Bouncing castles, ball pits, water slides, games.",
        "sort_order": 50,
    },
    {
        "slug": "food-fun",
        "name": "Food & Fun Extras",
        "short_description": "Popcorn, cotton candy, chocolate fountains.",
        "sort_order": 60,
    },
]


def seed_inventory_categories():
    for spec in DEFAULT_INVENTORY_CATEGORIES:
        if InventoryCategory.query.filter_by(slug=spec["slug"]).first():
            continue
        db.session.add(InventoryCategory(**spec))
    db.session.commit()
    print("Seeded inventory categories.")




from app.models import Setting, SettingCategory


DEFAULT_SETTINGS = [
    # ── Company ────────────────────────────────────────────────────
    {"key": "company_name", "label": "Company name",
     "category": SettingCategory.COMPANY,
     "description": "Shown on  emails, and the public site.",
     "value_text": "Funworld Events", "is_system": True},
    {"key": "company_tagline", "label": "Tagline",
     "category": SettingCategory.COMPANY,
     "description": "Short one-liner under the company name.",
     "value_text": "One-stop event partner", "is_system": True},
    {"key": "company_address", "label": "Address",
     "category": SettingCategory.COMPANY,
     "description": "Physical address shown on documents.",
     "value_text": "Nairobi, Kenya", "is_system": True},
    {"key": "company_phone", "label": "Phone",
     "category": SettingCategory.COMPANY,
     "description": "Primary contact number.",
     "value_text": "254785068486", "is_system": True},
    {"key": "company_email", "label": "Email",
     "category": SettingCategory.COMPANY,
     "description": "Primary contact email.",
     "value_text": "hello@funworld.example", "is_system": True},
    {"key": "company_kra_pin", "label": "KRA PIN",
     "category": SettingCategory.COMPANY,
     "description": "Tax PIN — .",
     "value_text": "", "is_system": True},
    {"key": "company_logo_url", "label": "Logo URL",
     "category": SettingCategory.COMPANY,
     "description": "URL or path to the company logo.",
     "value_text": "", "is_system": True},

    # ── Policies ───────────────────────────────────────────────────
    {"key": "privacy_policy", "label": "Privacy Policy",
     "category": SettingCategory.POLICY,
     "description": "Shown at /privacy. Markdown supported.",
     "value_text": "# Privacy Policy\n\nWe respect your privacy...",
     "is_system": True},
    {"key": "terms_of_service", "label": "Terms of Service",
     "category": SettingCategory.POLICY,
     "description": "Shown at /terms. Markdown supported.",
     "value_text": "# Terms of Service\n\nBy using this site...",
     "is_system": True},
    {"key": "refund_policy", "label": "Refund Policy",
     "category": SettingCategory.POLICY,
     "description": "Referenced in booking confirmations.",
     "value_text": "", "is_system": True},
    {"key": "cancellation_policy", "label": "Cancellation Policy",
     "category": SettingCategory.POLICY,
     "description": "Referenced in quotes and payments.",
     "value_text": "50% deposit is non-refundable within 14 days of the event.",
     "is_system": True},

    # ── Quote terms ────────────────────────────────────────────────
    {"key": "quote_default_terms", "label": "Default quote terms",
     "category": SettingCategory.QUOTE_TERMS,
     "description": "Pre-filled into every new quote version. Editable per-quote.",
     "value_text": (
         "50% deposit confirms the booking. "
         "Balance due 7 days before the event. "
         "Cancellations within 14 days of the event forfeit the deposit."
     ),
     "is_system": True},
    {"key": "quote_default_delivery_terms", "label": "Default quote delivery terms",
     "category": SettingCategory.QUOTE_TERMS,
     "description": "Pre-filled into every new quote version.",
     "value_text": (
         "Delivery and setup included within Nairobi. "
         "Outside Nairobi may incur a transport fee."
     ),
     "is_system": True},

    # ── payment terms ──────────────────────────────────────────────
    {"key": "payment_default_terms", "label": "Default payment terms",
     "category": SettingCategory.PAYMENT_TERMS,
     "description": "Pre-filled into every new payment.",
     "value_text": (
         "Payment due by the stated date. "
         "Please quote the payment number on your payment reference."
     ),
     "is_system": True},
    {"key": "Payment_methods", "label": "Payment instructions",
     "category": SettingCategory.PAYMENT_TERMS,
     "description": "Shown on every payment required.",
     "value_text": (
         "M-Pesa Paybill: ask us for the business number.\n"
         "Bank transfer: details on request.\n"
         "Always quote the payment number."
     ),
     "is_system": True},
]


def seed_settings():
    for spec in DEFAULT_SETTINGS:
        if Setting.query.filter_by(key=spec["key"]).first():
            continue
        db.session.add(Setting(**spec))
    db.session.commit()
    print(f"Seeded {len(DEFAULT_SETTINGS)} settings.")



