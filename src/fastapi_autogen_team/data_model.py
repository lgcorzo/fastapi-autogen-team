import time
from typing import List, Optional, Dict, Literal, Union, Any, Annotated

from pydantic import BaseModel, Field


class ImageUrl(BaseModel):
    url: str = Field(max_length=5000000)
    detail: Optional[str] = Field(default=None, max_length=100)


class ContentImage(BaseModel):
    type: Literal["image_url"]
    image_url: ImageUrl


class ContentText(BaseModel):
    type: Literal["text"]
    text: str = Field(max_length=50000)


class ModelInformation(BaseModel):
    id: str
    name: str
    description: str
    pricing: Dict[str, Any]
    context_length: int
    architecture: Dict[str, Any]
    top_provider: Dict[str, Any]
    per_request_limits: Optional[Dict[str, Any]]


class Message(BaseModel):
    role: str = Field(max_length=100)
    # Security: Use Annotated to enforce max_length on the list to prevent DoS via massive payloads
    content: Union[
        Annotated[str, Field(max_length=50000)],
        Annotated[List[Union[ContentText, ContentImage]], Field(max_length=100)],
    ]
    name: Optional[str] = Field(default=None, max_length=100)


class Input(BaseModel):
    model: str = Field(max_length=100)
    user: Optional[str] = Field(default="autogen_rag", max_length=100)
    messages: List[Message] = Field(max_length=100)
    temperature: float = Field(default=1, ge=0.0, le=2.0)
    top_p: float = Field(default=1, ge=0.0, le=1.0)
    presence_penalty: float = Field(default=0, ge=-2.0, le=2.0)
    frequency_penalty: float = Field(default=0, ge=-2.0, le=2.0)
    stream: bool = False


class Output(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, Any]
