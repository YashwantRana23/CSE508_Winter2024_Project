from fastapi import APIRouter

from app.schemas.chatbot import ChatRequest, ChatResponse
from app.services import chatbot_service

router = APIRouter(tags=["chatbot"])


@router.post("/chatbot/{domain}", response_model=ChatResponse)
def chat(domain: str, req: ChatRequest):
    """Domain-specific chatbot. Domain: murder, child, maternity, ipc, general."""
    response = chatbot_service.chat(domain, req.message, req.history)
    return ChatResponse(response=response, domain=domain)
