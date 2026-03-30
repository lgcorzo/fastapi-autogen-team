import pytest
from pydantic import ValidationError
from fastapi_autogen_team.data_model import Input

def test_image_url_length_limits():
    """Test that ImageUrl correctly limits the length of base64 URLs and details."""
    # This should fail due to url being too long
    with pytest.raises(ValidationError) as exc_info:
        Input(
            model="test",
            user="test",
            messages=[{"role": "user", "content": [{"type": "image_url", "image_url": {"url": "v" * 6000000}}]}],
            temperature=1.0,
            top_p=1.0,
            presence_penalty=0.0,
            frequency_penalty=0.0,
            stream=False
        )
    assert "String should have at most 5000000 characters" in str(exc_info.value)

    # This should fail due to detail being too long
    with pytest.raises(ValidationError) as exc_info:
        Input(
            model="test",
            user="test",
            messages=[{"role": "user", "content": [{"type": "image_url", "image_url": {"url": "valid_url", "detail": "high" * 100}}]}],
            temperature=1.0,
            top_p=1.0,
            presence_penalty=0.0,
            frequency_penalty=0.0,
            stream=False
        )
    assert "String should have at most 100 characters" in str(exc_info.value)

def test_image_url_valid_payload():
    """Test that a valid ImageUrl payload succeeds."""
    inp = Input(
        model="test",
        user="test",
        messages=[{"role": "user", "content": [{"type": "image_url", "image_url": {"url": "valid_url", "detail": "high"}}]}],
        temperature=1.0,
        top_p=1.0,
        presence_penalty=0.0,
        frequency_penalty=0.0,
        stream=False
    )
    assert inp.messages[0].content[0].image_url.url == "valid_url"
    assert inp.messages[0].content[0].image_url.detail == "high"
