from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.models import (
    Selection, SelectionNode, DocumentNode, Generation
)
from app.models.schemas import GenerationCreate, GenerationResponse, TestCase
from app.services.llm import generate_test_cases
from app.services.versioning import check_staleness

router = APIRouter(prefix="/api", tags=["generation"])


@router.post("/generate", response_model=GenerationResponse)
async def generate_test_cases_for_selection(
    data: GenerationCreate,
    db: AsyncSession = Depends(get_db),
):
    sel_result = await db.execute(
        select(Selection).where(Selection.id == data.selection_id)
    )
    selection = sel_result.scalar_one_or_none()
    if not selection:
        raise HTTPException(status_code=404, detail="Selection not found")

    nodes_result = await db.execute(
        select(DocumentNode).join(SelectionNode).where(
            SelectionNode.selection_id == selection.id
        )
    )
    nodes = nodes_result.scalars().all()
    if not nodes:
        raise HTTPException(status_code=400, detail="Selection has no nodes")

    existing_gen = await db.execute(
        select(Generation).where(
            Generation.selection_id == selection.id,
            Generation.node_id == nodes[0].id,
            Generation.node_version_id == selection.version_id,
        )
    )
    existing = existing_gen.scalar_one_or_none()

    combined_content = ""

    async def gather_content(node: DocumentNode, depth: int = 0):
        prefix = "#" * min(depth + 2, 4)
        combined_content = f"\n\n{prefix} {node.title or node.node_type}\n"
        if node.section_number:
            combined_content += f"Section: {node.section_number}\n"
        if node.body_text:
            combined_content += node.body_text + "\n"

        child_result = await db.execute(
            select(DocumentNode).where(DocumentNode.parent_id == node.id)
        )
        for child in child_result.scalars().all():
            combined_content += await gather_content(child, depth + 1)
        return combined_content

    for node in nodes:
        combined_content += await gather_content(node)

    result = await generate_test_cases(
        section_title=selection.name,
        section_number=", ".join(n.section_number for n in nodes if n.section_number),
        content=combined_content,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=502,
            detail=f"LLM generation failed: {result['error']}",
        )

    for tc in result["test_cases"]:
        if not tc.get("traced_to_section"):
            tc["traced_to_section"] = ", ".join(
                n.section_number for n in nodes if n.section_number
            )

    generation = Generation(
        selection_id=selection.id,
        node_id=nodes[0].id,
        node_version_id=selection.version_id,
        content_hash_at_generation=nodes[0].content_hash,
        test_cases=result["test_cases"],
        model_used=result.get("model_used", ""),
        prompt_used="",
        is_stale=False,
    )
    db.add(generation)
    await db.commit()
    await db.refresh(generation)

    current_node = (await db.execute(
        select(DocumentNode).where(DocumentNode.id == nodes[0].id)
    )).scalar_one_or_none()

    return GenerationResponse(
        id=generation.id,
        selection_id=generation.selection_id,
        node_id=generation.node_id,
        content_hash_at_generation=generation.content_hash_at_generation,
        current_content_hash=current_node.content_hash if current_node else "",
        is_stale=generation.is_stale,
        test_cases=[TestCase(**tc) for tc in result["test_cases"]],
        model_used=generation.model_used,
        generated_at=generation.generated_at,
    )


@router.get("/generations/{generation_id}", response_model=GenerationResponse)
async def get_generation(
    generation_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Generation).where(Generation.id == generation_id)
    )
    gen = result.scalar_one_or_none()
    if not gen:
        raise HTTPException(status_code=404, detail="Generation not found")

    await check_staleness(db, generation_id)
    await db.refresh(gen)

    node_result = await db.execute(
        select(DocumentNode).where(DocumentNode.id == gen.node_id)
    )
    current_node = node_result.scalar_one_or_none()

    return GenerationResponse(
        id=gen.id,
        selection_id=gen.selection_id,
        node_id=gen.node_id,
        content_hash_at_generation=gen.content_hash_at_generation,
        current_content_hash=current_node.content_hash if current_node else "",
        is_stale=gen.is_stale,
        test_cases=[TestCase(**tc) for tc in gen.test_cases],
        model_used=gen.model_used,
        generated_at=gen.generated_at,
    )


@router.get("/selections/{selection_id}/generations", response_model=List[GenerationResponse])
async def list_generations_for_selection(
    selection_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Generation).where(Generation.selection_id == selection_id)
    )
    gens = result.scalars().all()

    response = []
    for gen in gens:
        await check_staleness(db, gen.id)
        await db.refresh(gen)

        node_result = await db.execute(
            select(DocumentNode).where(DocumentNode.id == gen.node_id)
        )
        current_node = node_result.scalar_one_or_none()

        response.append(GenerationResponse(
            id=gen.id,
            selection_id=gen.selection_id,
            node_id=gen.node_id,
            content_hash_at_generation=gen.content_hash_at_generation,
            current_content_hash=current_node.content_hash if current_node else "",
            is_stale=gen.is_stale,
            test_cases=[TestCase(**tc) for tc in gen.test_cases],
            model_used=gen.model_used,
            generated_at=gen.generated_at,
        ))
    return response
