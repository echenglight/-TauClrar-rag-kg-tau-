from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.schemas.graph import GraphResponse


class FingerprintSummary(BaseModel):
    morgan_on_bits: int = 0
    maccs_on_bits: int = 0
    morgan_on_indices_preview: list[int] = Field(default_factory=list)
    maccs_on_indices_preview: list[int] = Field(default_factory=list)


class MoleculeProfile(BaseModel):
    name: str
    smiles: str
    molecular_formula: str
    descriptors: dict[str, Any] = Field(default_factory=dict)
    fingerprint: FingerprintSummary


class GNNPrediction(BaseModel):
    node_id: str
    node_name: str
    node_type: str
    score: float
    explanation: str


class GNNResult(BaseModel):
    model_name: str
    top_k: int
    predictions: list[GNNPrediction] = Field(default_factory=list)


class IntegratedSearchResponse(BaseModel):
    keyword: str
    kg: GraphResponse
    molecules: list[MoleculeProfile] = Field(default_factory=list)
    gnn: GNNResult
    notes: list[str] = Field(default_factory=list)
