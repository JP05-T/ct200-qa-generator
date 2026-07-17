import hashlib
from typing import List, Optional, Dict, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import (
    DocumentVersion, DocumentNode, Selection, SelectionNode, Generation,
    compute_content_hash,
)
from app.models.schemas import NodeDiff, VersionDiffSummary, SectionSummary
from app.services.parser import parse_pdf, TreeNode


async def ingest_document(
    db: AsyncSession, pdf_path: str, description: str = ""
) -> DocumentVersion:
    version_number_result = await db.execute(
        select(func.coalesce(func.max(DocumentVersion.version_number), 0))
    )
    max_version = version_number_result.scalar()
    new_version_num = max_version + 1

    version = DocumentVersion(
        version_number=new_version_num,
        source_file=pdf_path,
        description=description or f"Version {new_version_num}",
    )
    db.add(version)
    await db.flush()

    tree_nodes, tables = parse_pdf(pdf_path)

    node_map: Dict[str, DocumentNode] = {}

    async def persist_node(tree_node: TreeNode, parent_db: Optional[DocumentNode] = None):
        body = tree_node.body_text or ""
        title = tree_node.title or ""
        full_text = f"{title}\n{body}".strip()
        content_hash = compute_content_hash(full_text)

        db_node = DocumentNode(
            version_id=version.id,
            parent_id=parent_db.id if parent_db else None,
            node_type=tree_node.node_type,
            title=title,
            section_number=tree_node.section_number,
            heading_level=tree_node.heading_level,
            body_text=body,
            content_hash=content_hash,
            page_number=tree_node.page_number,
        )
        db.add(db_node)
        await db.flush()
        node_map[tree_node.title or body[:50]] = db_node

        for child in tree_node.children:
            await persist_node(child, db_node)

    for child in tree_nodes:
        await persist_node(child)

    await db.commit()
    await db.refresh(version)
    return version


async def match_nodes_v1_v2(
    db: AsyncSession, v1_id: int, v2_id: int
) -> VersionDiffSummary:
    v1_result = await db.execute(
        select(DocumentNode).where(DocumentNode.version_id == v1_id)
    )
    v1_nodes = {n.id: n for n in v1_result.scalars().all()}

    v2_result = await db.execute(
        select(DocumentNode).where(DocumentNode.version_id == v2_id)
    )
    v2_nodes = {n.id: n for n in v2_result.scalars().all()}

    v1_by_title = {}
    for n in v1_nodes.values():
        if not n.title and not n.section_number:
            continue
        key = n.title.strip() if n.title else n.body_text[:80].strip()
        v1_by_title[key] = n

    v2_by_title = {}
    for n in v2_nodes.values():
        if not n.title and not n.section_number:
            continue
        key = n.title.strip() if n.title else n.body_text[:80].strip()
        v2_by_title[key] = n

    added = []
    removed = []
    modified = []
    unchanged_ids = []

    for key, v2_node in v2_by_title.items():
        if key in v1_by_title:
            v1_node = v1_by_title[key]
            if v1_node.content_hash != v2_node.content_hash:
                modified.append(NodeDiff(
                    node_id=v2_node.id,
                    section_number=v2_node.section_number,
                    title=v2_node.title,
                    status="modified",
                    old_content_hash=v1_node.content_hash,
                    new_content_hash=v2_node.content_hash,
                    old_body_preview=v1_node.body_text[:150],
                    new_body_preview=v2_node.body_text[:150],
                ))
            else:
                unchanged_ids.append(v2_node.id)
        else:
            added.append(SectionSummary(
                id=v2_node.id,
                node_type=v2_node.node_type,
                title=v2_node.title,
                section_number=v2_node.section_number,
                heading_level=v2_node.heading_level,
                content_hash=v2_node.content_hash,
                child_count=0,
            ))

    for key, v1_node in v1_by_title.items():
        if key not in v2_by_title:
            removed.append(SectionSummary(
                id=v1_node.id,
                node_type=v1_node.node_type,
                title=v1_node.title,
                section_number=v1_node.section_number,
                heading_level=v1_node.heading_level,
                content_hash=v1_node.content_hash,
                child_count=0,
            ))

    return VersionDiffSummary(
        v1_id=v1_id,
        v2_id=v2_id,
        added_nodes=added,
        removed_nodes=removed,
        modified_nodes=modified,
        unchanged_nodes=unchanged_ids,
    )


async def check_staleness(
    db: AsyncSession, generation_id: int
) -> Optional[Dict]:
    result = await db.execute(
        select(Generation).where(Generation.id == generation_id)
    )
    gen = result.scalar_one_or_none()
    if not gen:
        return None

    node_result = await db.execute(
        select(DocumentNode).where(DocumentNode.id == gen.node_id)
    )
    current_node = node_result.scalar_one_or_none()
    if not current_node:
        return {
            "is_stale": True,
            "reason": "node_not_found",
            "current_hash": "",
            "generation_hash": gen.content_hash_at_generation,
        }

    is_stale = current_node.content_hash != gen.content_hash_at_generation

    if is_stale:
        gen.is_stale = True
        await db.flush()

    return {
        "is_stale": is_stale,
        "current_hash": current_node.content_hash,
        "generation_hash": gen.content_hash_at_generation,
    }
