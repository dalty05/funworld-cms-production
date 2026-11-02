import time
from datetime import timedelta

import click
from flask import Flask

from app import db
from app.models import (
    AuditLog,
    IdempotencyKey,
    Role,
    RoleAssignment,
    TimelineEvent,
    User,
    utcnow,
)
from app.security import hash_password, PasswordPolicyError


# ---------------------------------------------------------------------------
# SEEDING
# ---------------------------------------------------------------------------


@click.command("seed-all")
def seed_all_cli():
    """Seed permissions, roles templates."""
    from app.seeds import (
        seed_permissions_and_roles,
        
        seed_blog_categories,
        seed_blog_tags,
        seed_service_categories,
        seed_inventory_categories,
        seed_settings,
    )

    click.echo("Seeding permissions and roles...")
    seed_permissions_and_roles()



    click.echo("Seeding blog templates...")
    seed_blog_categories()
    click.echo("Seed complete.")


    click.echo("Seeding blog tags templates...")
    seed_blog_tags()
    click.echo("Seed complete.")

    click.echo("Seeding service categories templates...")
    seed_service_categories()
    click.echo("Seed complete.")

    click.echo("Seeding inventory categories templates...")
    seed_inventory_categories()
    click.echo("Seed complete.")

    click.echo("Seeding settings templates...")
    seed_settings()
    click.echo("Seed complete.")

# ---------------------------------------------------------------------------
# OWNER
# ---------------------------------------------------------------------------

@click.command("create-owner")
@click.option("--email", prompt=True)
@click.option("--full-name", prompt="Full name")
@click.option(
    "--password",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
)
def create_owner(email: str, full_name: str, password: str):
    """Create the first owner user and assign the Owner role."""
    email = email.lower().strip()

    if User.query.filter_by(email=email).first():
        click.echo(f"User {email} already exists.")
        return

    owner_role = Role.query.filter_by(slug="owner").first()

    if not owner_role:
        click.echo("Owner role not found. Run 'flask seed-all' first.")
        return

    try:
        password_hash = hash_password(password)
    except PasswordPolicyError as exc:
        raise click.ClickException(str(exc)) from exc

    user = User(
        email=email,
        full_name=full_name,
        password_hash=password_hash,
        is_active=True,
        is_verified=True,
    )

    db.session.add(user)
    db.session.flush()

    db.session.add(
        RoleAssignment(
            user_id=user.id,
            role_id=owner_role.id,
            scope_type="global",
            is_active=True,
        )
    )

    db.session.commit()

    click.echo(f"Owner created: {email}")



# ---------------------------------------------------------------------------
# RETENTION / PURGING
# ---------------------------------------------------------------------------

RETENTION_YEARS = 7


def _cutoff():
    return utcnow() - timedelta(days=RETENTION_YEARS * 365)


@click.command("purge-old-records")
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would be deleted without deleting anything.",
)
def purge_old_records(dry_run):
    """Delete records older than the retention window."""
    cutoff = _cutoff()

    timeline_count = TimelineEvent.query.filter(
        TimelineEvent.created_at < cutoff
    ).count()

    audit_count = AuditLog.query.filter(
        AuditLog.created_at < cutoff
    ).count()

    idem_count = IdempotencyKey.query.filter(
        IdempotencyKey.expires_at < utcnow()
    ).count()

    click.echo(f"Cutoff: {cutoff.isoformat()}")
    click.echo(f"Timeline events to delete: {timeline_count}")
    click.echo(f"Audit rows to delete:      {audit_count}")
    click.echo(f"Expired idempotency rows:  {idem_count}")

    if dry_run:
        click.echo("Dry run — nothing deleted.")
        return

    TimelineEvent.query.filter(
        TimelineEvent.created_at < cutoff
    ).delete(synchronize_session=False)

    AuditLog.query.filter(
        AuditLog.created_at < cutoff
    ).delete(synchronize_session=False)

    IdempotencyKey.query.filter(
        IdempotencyKey.expires_at < utcnow()
    ).delete(synchronize_session=False)

    db.session.commit()

    click.echo("Purge complete.")



@click.command("publish-scheduled-posts")
def publish_scheduled_cli():
    from app.services import publish_due_scheduled_posts
    n = publish_due_scheduled_posts()
    click.echo(f"Published {n} scheduled post(s).")



import click


# ---------------------------------------------------------------------------
# CLI REGISTRATION
# ---------------------------------------------------------------------------



def register_cli(app: Flask):
    """Register application-specific Flask CLI commands."""

    app.cli.add_command(seed_all_cli)
    app.cli.add_command(create_owner)
    app.cli.add_command(purge_old_records)
    app.cli.add_command(publish_scheduled_cli)


