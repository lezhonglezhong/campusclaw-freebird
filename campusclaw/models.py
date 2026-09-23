"""Persistence models for classes, users, and teaching materials."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from campusclaw.db import Base


class Class(Base):
    """A class which owns users and teaching materials."""

    __tablename__ = "classes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    users: Mapped[list[User]] = relationship(back_populates="class_")
    materials: Mapped[list[Material]] = relationship(back_populates="class_")


class User(Base):
    """An account with exactly one role and class membership."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), nullable=False)
    class_: Mapped[Class] = relationship(back_populates="users")
    uploaded_materials: Mapped[list[Material]] = relationship(back_populates="uploader")


class Material(Base):
    """A class-owned local knowledge-base material record."""

    __tablename__ = "materials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), nullable=False)
    uploader_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    content_path: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    class_: Mapped[Class] = relationship(back_populates="materials")
    uploader: Mapped[User] = relationship(back_populates="uploaded_materials")
