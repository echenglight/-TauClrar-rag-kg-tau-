from __future__ import annotations

from fastapi import APIRouter

from app.schemas.template import TemplateDetailResponse, TemplateListResponse
from app.services.template_graph_service import TemplateGraphService

router = APIRouter(prefix="/api/templates", tags=["templates"])

template_service = TemplateGraphService()


@router.get("", response_model=TemplateListResponse)
def list_templates() -> TemplateListResponse:
    return template_service.list_templates()


@router.get("/{template_id}", response_model=TemplateDetailResponse)
def get_template(template_id: str) -> TemplateDetailResponse:
    return template_service.get_template(template_id)
