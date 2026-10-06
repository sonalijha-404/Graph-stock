from fastapi import APIRouter

from app.schemas.chat import ChatRequest, ChatResponse, ImpactSimulateRequest
from app.services.chat import handle_chat, handle_impact_simulate

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest) -> ChatResponse:
    return handle_chat(body.question)


@router.post("/impact/simulate", response_model=ChatResponse)
def impact_simulate(body: ImpactSimulateRequest) -> ChatResponse:
    return handle_impact_simulate(body)
