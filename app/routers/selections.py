from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.database import get_db
from app.models.models import Selection, SelectionNode, DocumentNode, DocumentVersion
from app.models.schemas import SelectionCreate, SelectionResponse, NodeResponse

router = APIRouter(prefix="/api", tags=["selections"])


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


@router.post("/selections", response_model=SelectionResponse)
async def create_selection(
    data: SelectionCreate,
    db: AsyncSession = Depends(get_db),
):
    ver_result = await db.execute(
        select(DocumentVersion).where(DocumentVersion.id == data.version_id)
    )
    if not ver_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Version not found")

    selection = Selection(
        name=data.name,
        version_id=data.version_id,
    )
    db.add(selection)
    await db.flush()

    for nid in data.node_ids:
        node_result = await db.execute(
            select(DocumentNode).where(DocumentNode.id == nid)
        )
        node = node_result.scalar_one_or_none()
        if not node:
            raise HTTPException(
                status_code=404,
                detail=f"Node {nid} not found",
            )
        link = SelectionNode(selection_id=selection.id, node_id=nid)
        db.add(link)

    await db.commit()
    await db.refresh(selection)

    nodes_result = await db.execute(
        select(DocumentNode).join(SelectionNode).where(
            SelectionNode.selection_id == selection.id
        )
    )
    nodes = nodes_result.scalars().all()

    return SelectionResponse(
        id=selection.id,
        name=selection.name,
        version_id=selection.version_id,
        created_at=selection.created_at,
        nodes=[node_to_response(n) for n in nodes],
    )


@router.get("/selections/{selection_id}", response_model=SelectionResponse)
async def get_selection(
    selection_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Selection).where(Selection.id == selection_id)
    )
    selection = result.scalar_one_or_none()
    if not selection:
        raise HTTPException(status_code=404, detail="Selection not found")

    nodes_result = await db.execute(
        select(DocumentNode).join(SelectionNode).where(
            SelectionNode.selection_id == selection.id
        )
    )
    nodes = nodes_result.scalars().all()

    return SelectionResponse(
        id=selection.id,
        name=selection.name,
        version_id=selection.version_id,
        created_at=selection.created_at,
        nodes=[node_to_response(n) for n in nodes],
    )


@router.get("/selections", response_model=List[SelectionResponse])
async def list_selections(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Selection).order_by(Selection.created_at.desc()))
    selections = result.scalars().all()

    response = []
    for sel in selections:
        nodes_result = await db.execute(
            select(DocumentNode).join(SelectionNode).where(
                SelectionNode.selection_id == sel.id
            )
        )
        nodes = nodes_result.scalars().all()
        response.append(SelectionResponse(
            id=sel.id,
            name=sel.name,
            version_id=sel.version_id,
            created_at=sel.created_at,
            nodes=[node_to_response(n) for n in nodes],
        ))
    return response
