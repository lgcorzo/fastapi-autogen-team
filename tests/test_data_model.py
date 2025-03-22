import pytest
from pydantic import ValidationError

from fastapi_autogen_team.data_model import Input, Message, ModelInformation, Output


def test_model_information_valid():
    """Test that a valid ModelInformation object can be created."""
    model_info = ModelInformation(
        id="test_id",
        name="test_model",
        description="A test model",
        pricing={"prompt": "0.01", "completion": "0.02"},
        context_length=2048,
        architecture={"modality": "text", "tokenizer": "test_tokenizer"},
        top_provider={"max_completion_tokens": 1000, "is_moderated": True},
        per_request_limits={"max_requests": 100},
    )
    assert model_info.id == "test_id"
    assert model_info.name == "test_model"
    assert model_info.pricing["completion"] == "0.02"


def test_model_information_missing_field():
    """Test that ModelInformation raises ValidationError when a required field is missing."""
    with pytest.raises(ValidationError):
        ModelInformation(
            name="test_model",
            description="A test model",
            pricing={"prompt": "0.01", "completion": "0.02"},
            context_length=2048,
            architecture={"modality": "text", "tokenizer": "test_tokenizer"},
            top_provider={"max_completion_tokens": 1000, "is_moderated": True},
            per_request_limits={"max_requests": 100},
        )


def test_message_valid():
    """Test that a valid Message object can be created."""
    message = Message(role="user", content="Hello, world!")
    assert message.role == "user"
    assert message.content == "Hello, world!"


def test_message_missing_field():
    """Test that Message raises ValidationError when a required field is missing."""
    with pytest.raises(ValidationError):
        Message(role="user")


def test_input_valid():
    """Test that a valid Input object can be created with default values."""
    message = Message(role="user", content="Hello, world!")
    input_data = Input(model="test_model", messages=[message])
    assert input_data.model == "test_model"
    assert input_data.temperature == 1
    assert input_data.top_p == 1
    assert input_data.presence_penalty == 0
    assert input_data.frequency_penalty == 0
    assert input_data.stream == True


def test_input_custom_values():
    """Test that an Input object can be created with custom values."""
    message = Message(role="user", content="Translate to French")
    input_data = Input(
        model="custom_model",
        messages=[message],
        temperature=0.7,
        top_p=0.5,
        presence_penalty=0.5,
        frequency_penalty=0.5,
        stream=False,
    )
    assert input_data.model == "custom_model"
    assert input_data.temperature == 0.7
    assert input_data.stream == False


def test_input_missing_field():
    """Test that Input raises ValidationError when a required field is missing."""
    with pytest.raises(ValidationError):
        Input(messages=[{"role": "user", "content": "hello"}])


def test_output_valid():
    """Test that a valid Output object can be created."""
    output = Output(
        id="test_id",
        model="test_model",
        choices=[{"text": "This is a test"}],
        usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    )
    assert output.id == "test_id"
    assert output.object == "chat.completion"
    assert output.model == "test_model"
    assert len(output.choices) == 1
    assert output.usage["total_tokens"] == 15


def test_output_missing_field():
    """Test that Output raises ValidationError when a required field is missing."""
    with pytest.raises(ValidationError):
        Output(
            model="test_model",
            choices=[{"text": "This is a test"}],
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        )
