import time
from typing import List, Optional, Dict, Literal, Union, Any

from pydantic import BaseModel, Field


class ContentImage(BaseModel):
    type: Literal["image_url"]
    image_url: Dict[str, str]  # {"url": "data:image/png;base64,..."}


class ContentText(BaseModel):
    type: Literal["text"]
    text: str


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
    role: str
    content: Union[str, List[Union[ContentText, ContentImage]]]
    name: Optional[str] = None


class Input(BaseModel):
    model: str
    user: Optional[str] = "autogen_rag"
    messages: List[Message]
    temperature: float = 1
    top_p: float = 1
    presence_penalty: float = 0
    frequency_penalty: float = 0
    stream: bool = False


class Output(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, Any]
