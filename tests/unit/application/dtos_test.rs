use fastapi_autogen_team::application::dtos::*;
use serde_json::json;

#[test]
fn test_model_information_valid() {
    let json_data = json!({
        "id": "test_id",
        "name": "test_name",
        "description": "test_desc",
        "pricing": {"prompt": "0.01", "completion": "0.02"},
        "context_length": 2048,
        "architecture": {"modality": "text", "tokenizer": "test_tokenizer"},
        "top_provider": {"max_completion_tokens": 1000, "is_moderated": true},
        "per_request_limits": {"max_requests": 100}
    });

    let model_info: ModelInformation = serde_json::from_value(json_data).unwrap();
    assert_eq!(model_info.id, "test_id");
    assert_eq!(model_info.name, "test_name");
}

#[test]
fn test_message_valid() {
    let msg = Message {
        role: "user".to_string(),
        content: ContentType::String("Hello, world!".to_string()),
        name: None,
    };
    assert_eq!(msg.role, "user");
}

#[test]
fn test_input_valid() {
    let json_data = json!({
        "model": "test_model",
        "messages": [{"role": "user", "content": "Hello, world!"}]
    });

    let input: Input = serde_json::from_value(json_data).unwrap();
    assert_eq!(input.model, "test_model");
    assert_eq!(input.messages.len(), 1);
}

#[test]
fn test_content_type_list() {
    let json_data = json!([
        {"type": "text", "text": "Hello"},
        {"type": "image_url", "image_url": {"url": "http://test.com"}}
    ]);

    let content: ContentType = serde_json::from_value(json_data).unwrap();
    match content {
        ContentType::List(list) => {
            assert_eq!(list.len(), 2);
            match &list[0] {
                Content::Text { text } => assert_eq!(text, "Hello"),
                _ => panic!("Expected Text"),
            }
        }
        _ => panic!("Expected List"),
    }
}

#[test]
fn test_output_default() {
    let output = Output::default();
    assert_eq!(output.object, "chat.completion");
    assert!(output.created > 0);
    assert!(output.choices.is_empty());
}
