from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import Subgraph


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)


class CalculationTrace(BaseModel):
    label: str
    expression: str
    value: float


class ExecutionMs(BaseModel):
    neo4j: int = 0
    calculation: int = 0
    total: int = 0


class ChatResponse(BaseModel):
    answer: str
    intent: str
    entities: dict[str, Any] = Field(default_factory=dict)
    cypher: str = ""
    parameters: dict[str, Any] = Field(default_factory=dict)
    subgraph: Subgraph = Field(default_factory=Subgraph)
    results: list[dict[str, Any]] = Field(default_factory=list)
    calculations: list[CalculationTrace] = Field(default_factory=list)
    stages: list[str] = Field(default_factory=list)
    execution_ms: ExecutionMs = Field(default_factory=ExecutionMs)
    disclaimer: str = ""


class ImpactSimulateRequest(BaseModel):
    scope: str  # stock | sector
    symbol: str | None = None
    sector: str | None = None
    change_percent: float
