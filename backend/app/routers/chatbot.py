import logging
from fastapi import APIRouter, HTTPException
from app.schemas.chatbot import ChatRequest, ChatResponse, Domain
from app.services import chatbot_service

router = APIRouter(tags=["chatbot"])
logger = logging.getLogger(__name__)


@router.get("/chatbot/status")
def status():
    return {domain: chatbot_service.domain_status(domain) for domain in ("murder", "child", "maternity", "ipc", "general")}


@router.post("/chatbot/{domain}", response_model=ChatResponse)
def chat(domain: Domain, req: ChatRequest):
    if req.domain and req.domain != domain:
        raise HTTPException(422, "The selected domain does not match the request.")
    availability = chatbot_service.domain_status(domain)
    if not availability["available"]:
        raise HTTPException(503, availability["reason"])
    try:
        result = chatbot_service.chat(
            domain, req.message, [item.model_dump() for item in req.history],
            method=req.method, answer_mode=req.answer_mode,
        )
        logger.info("Chat response request_id=%s mode=%s domain=%s", result["request_id"], result["mode"], domain)
        return result
    except (ValueError, OSError):
        raise HTTPException(503, "The selected source could not be loaded. Check its PDF configuration and extractable text.")
    except Exception:
        # Never include provider credentials, request text or raw API error bodies.
        logger.error("Chatbot request failed before a usable response was produced.")
        raise HTTPException(503, "The assistant is unavailable. Check the local source and model configuration.")
