import logging
from fastapi import APIRouter, HTTPException
from openai import AuthenticationError, RateLimitError
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
        response = chatbot_service.chat(domain, req.message, [item.model_dump() for item in req.history])
    except RateLimitError as error:
        if error.code in ("insufficient_quota", "credit_balance_exhausted"):
            raise HTTPException(503, "OpenAI API credits are exhausted. Add credits to the API project, then retry. Search and graph generation remain available.")
        raise HTTPException(503, "The AI provider is temporarily rate-limited. Please retry shortly.")
    except AuthenticationError:
        raise HTTPException(503, "The AI provider rejected the configured API key. Update the backend API key and restart the server.")
    except Exception:
        logger.exception("Chatbot request failed")
        raise HTTPException(503, "The assistant is unavailable. Check the server configuration and logs.")
    return ChatResponse(response=response, domain=domain)
