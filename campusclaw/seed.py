"""Repeatable local development data."""

from flask import Flask
from werkzeug.security import generate_password_hash

from campusclaw.models import Class, Material, User


SEED_ACCOUNTS = {
    "teacher-a": {"password": "teacher-a-password", "role": "teacher", "class_name": "A"},
    "student-a": {"password": "student-a-password", "role": "student", "class_name": "A"},
}


def seed_data(app: Flask) -> None:
    """Create the fixed local sample data without duplicating existing rows."""
    session = app.extensions["sqlalchemy"]["session"]
    classes = {}
    for name in ("A", "B"):
        class_ = session.query(Class).filter_by(name=name).one_or_none()
        if class_ is None:
            class_ = Class(name=name)
            session.add(class_)
        classes[name] = class_
    session.flush()

    for account, details in SEED_ACCOUNTS.items():
        if session.query(User).filter_by(account=account).one_or_none() is None:
            session.add(
                User(
                    account=account,
                    password_hash=generate_password_hash(details["password"]),
                    role=details["role"],
                    class_=classes[details["class_name"]],
                )
            )
    session.flush()

    teacher = session.query(User).filter_by(account="teacher-a").one()
    for class_name in ("A", "B"):
        class_ = classes[class_name]
        if session.query(Material).filter_by(class_id=class_.id).first() is None:
            session.add(
                Material(
                    display_name=f"Class {class_name} sample material",
                    class_=class_,
                    uploader=teacher,
                    content_path=f"seed/class-{class_name.lower()}.txt",
                    status="ready",
                )
            )
    session.commit()


def register_seed_command(app: Flask) -> None:
    """Expose seeding as ``flask --app campusclaw seed``."""

    @app.cli.command("seed")
    def seed_command() -> None:
        seed_data(app)
