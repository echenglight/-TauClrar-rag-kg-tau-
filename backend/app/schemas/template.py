from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.graph import GraphResponse


class TemplateSummary(BaseModel):
    id: str
    title: str
    description: str


class TemplateListResponse(BaseModel):
    templates: list[TemplateSummary] = Field(default_factory=list)


class TemplateDetailResponse(BaseModel):
    id: str
    title: str
    description: str
    relation_legend: dict[str, str] = Field(default_factory=dict)
    graph: GraphResponse
