import hashlib
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean, JSON
)
from sqlalchemy.orm import relationship
from app.models.database import Base


def compute_content_hash(text: str) -> str:
    normalized = " ".join(text.split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    version_number = Column(Integer, nullable=False, unique=True)
    source_file = Column(String(512), nullable=False)
    description = Column(String(1024), default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    nodes = relationship("DocumentNode", back_populates="version", cascade="all, delete-orphan")
    selections = relationship("Selection", back_populates="version", cascade="all, delete-orphan")


class DocumentNode(Base):
    __tablename__ = "document_nodes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    version_id = Column(Integer, ForeignKey("document_versions.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("document_nodes.id"), nullable=True)

    node_type = Column(String(50), nullable=False)
    title = Column(Text, default="")
    section_number = Column(String(50), default="")
    heading_level = Column(Integer, default=0)
    body_text = Column(Text, default="")
    content_hash = Column(String(64), nullable=False)
    page_number = Column(Integer, default=0)

    version = relationship("DocumentVersion", back_populates="nodes")
    children = relationship("DocumentNode", backref="parent", remote_side=[id])

    @staticmethod
    def from_text(body_text: str) -> str:
        return compute_content_hash(body_text)


class Selection(Base):
    __tablename__ = "selections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(256), nullable=False)
    version_id = Column(Integer, ForeignKey("document_versions.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    version = relationship("DocumentVersion", back_populates="selections")
    node_links = relationship("SelectionNode", back_populates="selection", cascade="all, delete-orphan")
    generations = relationship("Generation", back_populates="selection", cascade="all, delete-orphan")


class SelectionNode(Base):
    __tablename__ = "selection_nodes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    selection_id = Column(Integer, ForeignKey("selections.id"), nullable=False)
    node_id = Column(Integer, ForeignKey("document_nodes.id"), nullable=False)

    selection = relationship("Selection", back_populates="node_links")
    node = relationship("DocumentNode")


class Generation(Base):
    __tablename__ = "generations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    selection_id = Column(Integer, ForeignKey("selections.id"), nullable=False)
    node_id = Column(Integer, ForeignKey("document_nodes.id"), nullable=False)
    node_version_id = Column(Integer, ForeignKey("document_versions.id"), nullable=False)
    content_hash_at_generation = Column(String(64), nullable=False)
    test_cases = Column(JSON, nullable=False)
    model_used = Column(String(128), default="")
    prompt_used = Column(Text, default="")
    generated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_stale = Column(Boolean, default=False)

    selection = relationship("Selection", back_populates="generations")
    node = relationship("DocumentNode")
