from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

Domain = Literal["murder", "child", "maternity", "ipc", "general"]

class ChatMessage(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=12000)

class ChatRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    domain: Domain | None = None
    message: str = Field(min_length=1, max_length=4000)
    history: list[ChatMessage] = Field(default_factory=list, max_length=40)

class ChatResponse(BaseModel):
    response: str
    domain: str
