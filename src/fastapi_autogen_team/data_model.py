import time
from typing import List, Optional, Dict, Literal, Union, Any, Annotated

from pydantic import BaseModel, Field


class ContentImage(BaseModel):
    type: Literal["image_url"]
    image_url: Dict[str, str]  # {"url": "data:image/png;base64,..."}


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
    content: Union[Annotated[str, Field(max_length=50000)], Annotated[List[Union[ContentText, ContentImage]], Field(max_length=100)]]
    name: Optional[str] = Field(default=None, max_length=100)


class Input(BaseModel):
    model: str = Field(max_length=100)
    user: Optional[str] = Field(default="autogen_rag", max_length=100)
    messages: List[Message] = Field(max_length=100)
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
