import time
from typing import List, Optional, Dict, Literal, Union

from pydantic import BaseModel

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
    pricing: dict
    context_length: int
    architecture: dict
    top_provider: dict
    per_request_limits: Optional[dict]


class Message(BaseModel):
    role: str
    content: Union[str, List[Union[ContentText, ContentImage]]]


class Input(BaseModel):
    model: str
    messages: List[Message]
    temperature: float = 1
    top_p: float = 1
    presence_penalty: float = 0
    frequency_penalty: float = 0
    stream: bool = False


class Output(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int = int(time.time())
    model: str
    choices: List
    usage: dict
