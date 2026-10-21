"""Persistence models for classes, users, and teaching materials."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from campusclaw.db import Base


class Class(Base):
    """A class which owns users and teaching materials."""

    __tablename__ = "classes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    users: Mapped[list[User]] = relationship(back_populates="class_")
    materials: Mapped[list[Material]] = relationship(back_populates="class_")
    knowledge_entries: Mapped[list[KnowledgeEntry]] = relationship(back_populates="class_")
    knowledge_chunks: Mapped[list[KnowledgeChunk]] = relationship(back_populates="class_")


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
    knowledge_entry: Mapped[KnowledgeEntry | None] = relationship(
        back_populates="material", cascade="all, delete-orphan", uselist=False
    )


class KnowledgeEntry(Base):
    """The authoritative original text retained separately from its chunks."""

    __tablename__ = "knowledge_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id", ondelete="CASCADE"), unique=True, nullable=False)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), nullable=False)
    body_text: Mapped[str] = mapped_column(Text, nullable=False)
    strategy: Mapped[str] = mapped_column(String(32), nullable=False, default="auto")
    preprocessing: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    text_status: Mapped[str] = mapped_column(String(32), nullable=False, default="ready")
    vector_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    material: Mapped[Material] = relationship(back_populates="knowledge_entry")
    class_: Mapped[Class] = relationship(back_populates="knowledge_entries")
    chunks: Mapped[list[KnowledgeChunk]] = relationship(
        back_populates="entry", cascade="all, delete-orphan", order_by="KnowledgeChunk.chunk_index"
    )


class KnowledgeChunk(Base):
    """A traceable, class-scoped retrieval unit with independent index state."""

    __tablename__ = "knowledge_chunks"
    __table_args__ = (UniqueConstraint("knowledge_entry_id", "chunk_index", name="uq_entry_chunk_index"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    knowledge_entry_id: Mapped[int] = mapped_column(ForeignKey("knowledge_entries.id", ondelete="CASCADE"), nullable=False)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id", ondelete="CASCADE"), nullable=False)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    start_offset: Mapped[int] = mapped_column(Integer, nullable=False)
    end_offset: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    text_status: Mapped[str] = mapped_column(String(32), nullable=False, default="ready")
    vector_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    entry: Mapped[KnowledgeEntry] = relationship(back_populates="chunks")
    class_: Mapped[Class] = relationship(back_populates="knowledge_chunks")


class PromptTemplate(Base):
    """Reusable teacher-authored prompt, visible only within its class."""
    __tablename__ = 'prompt_templates'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    class_id: Mapped[int] = mapped_column(ForeignKey('classes.id'), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
