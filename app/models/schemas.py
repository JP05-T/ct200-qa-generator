from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, Field


class NodeResponse(BaseModel):
    id: int
    node_type: str
    title: str
    section_number: str
    heading_level: int
    body_text: str
    content_hash: str
    page_number: int
    children: List["NodeResponse"] = []

    class Config:
        from_attributes = True


class NodeDiff(BaseModel):
    node_id: int
    section_number: str
    title: str
    status: str
    old_content_hash: Optional[str] = None
    new_content_hash: Optional[str] = None
    old_body_preview: Optional[str] = None
    new_body_preview: Optional[str] = None


class VersionSummary(BaseModel):
    id: int
    version_number: int
    source_file: str
    description: str
    created_at: datetime
    node_count: int = 0


class SectionSummary(BaseModel):
    id: int
    node_type: str
    title: str
    section_number: str
    heading_level: int
    content_hash: str
    child_count: int = 0


class SelectionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    node_ids: List[int] = Field(..., min_length=1)
    version_id: int


class SelectionResponse(BaseModel):
    id: int
    name: str
    version_id: int
    created_at: datetime
    nodes: List[NodeResponse] = []

    class Config:
        from_attributes = True


class TestCase(BaseModel):
    id: str
    title: str
    description: str
    preconditions: str
    steps: List[str]
    expected_result: str
    priority: str = "medium"
    traced_to_section: str = ""


class GenerationResponse(BaseModel):
    id: int
    selection_id: int
    node_id: int
    content_hash_at_generation: str
    current_content_hash: str
    is_stale: bool
    test_cases: List[TestCase]
    model_used: str
    generated_at: datetime


class GenerationCreate(BaseModel):
    selection_id: int


class SearchResult(BaseModel):
    id: int
    node_type: str
    title: str
    section_number: str
    heading_level: int
    body_preview: str
    content_hash: str


class VersionDiffSummary(BaseModel):
    v1_id: int
    v2_id: int
    added_nodes: List[SectionSummary]
    removed_nodes: List[SectionSummary]
    modified_nodes: List[NodeDiff]
    unchanged_nodes: List[int]


class ErrorResponse(BaseModel):
    detail: str
