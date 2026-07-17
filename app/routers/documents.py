from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.database import get_db
from app.models.models import DocumentVersion, DocumentNode, Selection, SelectionNode
from app.models.schemas import (
    NodeResponse, VersionSummary, SectionSummary, VersionDiffSummary, SearchResult
)
from app.services.versioning import ingest_document, match_nodes_v1_v2

router = APIRouter(prefix="/api", tags=["documents"])


def node_to_response(node: DocumentNode) -> NodeResponse:
    return NodeResponse(
        id=node.id,
        node_type=node.node_type,
        title=node.title or "",
        section_number=node.section_number or "",
        heading_level=node.heading_level,
        body_text=node.body_text or "",
        content_hash=node.content_hash,
        page_number=node.page_number,
        children=[],
    )


def build_node_tree(node: DocumentNode, all_nodes: dict) -> NodeResponse:
    resp = node_to_response(node)
    children = [
        build_node_tree(child, all_nodes)
        for child in all_nodes.values()
        if child.parent_id == node.id
    ]
    resp.children = children
    return resp


@router.get("/documents", response_model=List[VersionSummary])
async def list_documents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DocumentVersion).order_by(DocumentVersion.version_number)
    )
    versions = result.scalars().all()
    response = []
    for v in versions:
        count_result = await db.execute(
            select(func.count(DocumentNode.id)).where(DocumentNode.version_id == v.id)
        )
        node_count = count_result.scalar() or 0
        response.append(VersionSummary(
            id=v.id,
            version_number=v.version_number,
            source_file=v.source_file,
            description=v.description or "",
            created_at=v.created_at,
            node_count=node_count,
        ))
    return response


@router.post("/documents/ingest", response_model=VersionSummary)
async def ingest_new_version(
    pdf_path: str = Query(..., description="Path to PDF file"),
    description: str = Query("", description="Version description"),
    db: AsyncSession = Depends(get_db),
):
    version = await ingest_document(db, pdf_path, description)
    count_result = await db.execute(
        select(func.count(DocumentNode.id)).where(DocumentNode.version_id == version.id)
    )
    node_count = count_result.scalar() or 0
    return VersionSummary(
        id=version.id,
        version_number=version.version_number,
        source_file=version.source_file,
        description=version.description or "",
        created_at=version.created_at,
        node_count=node_count,
    )


@router.get("/versions/{version_id}/sections", response_model=List[SectionSummary])
async def list_top_level_sections(
    version_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DocumentNode).where(
            DocumentNode.version_id == version_id,
            DocumentNode.parent_id.is_(None),
        )
    )
    nodes = result.scalars().all()

    response = []
    for n in nodes:
        child_count_result = await db.execute(
            select(func.count(DocumentNode.id)).where(DocumentNode.parent_id == n.id)
        )
        child_count = child_count_result.scalar() or 0
        response.append(SectionSummary(
            id=n.id,
            node_type=n.node_type,
            title=n.title or "",
            section_number=n.section_number or "",
            heading_level=n.heading_level,
            content_hash=n.content_hash,
            child_count=child_count,
        ))
    return response


@router.get("/nodes/search", response_model=List[SearchResult])
async def search_nodes(
    q: str = Query(..., min_length=1),
    version_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(DocumentNode)
    if version_id:
        query = query.where(DocumentNode.version_id == version_id)

    like_pattern = f"%{q}%"
    query = query.where(
        or_(
            DocumentNode.title.ilike(like_pattern),
            DocumentNode.body_text.ilike(like_pattern),
            DocumentNode.section_number.ilike(like_pattern),
        )
    )

    result = await db.execute(query)
    nodes = result.scalars().all()

    return [
        SearchResult(
            id=n.id,
            node_type=n.node_type,
            title=n.title or "",
            section_number=n.section_number or "",
            heading_level=n.heading_level,
            body_preview=(n.body_text or "")[:200],
            content_hash=n.content_hash,
        )
        for n in nodes
    ]


@router.get("/nodes/{node_id}", response_model=NodeResponse)
async def get_node(node_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DocumentNode).where(DocumentNode.id == node_id)
    )
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    all_nodes_result = await db.execute(
        select(DocumentNode).where(DocumentNode.version_id == node.version_id)
    )
    all_nodes = {n.id: n for n in all_nodes_result.scalars().all()}
    return build_node_tree(node, all_nodes)


@router.get("/versions/{v1_id}/diff/{v2_id}", response_model=VersionDiffSummary)
async def get_version_diff(
    v1_id: int, v2_id: int, db: AsyncSession = Depends(get_db)
):
    return await match_nodes_v1_v2(db, v1_id, v2_id)
