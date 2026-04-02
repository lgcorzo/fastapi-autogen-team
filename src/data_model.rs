use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::HashMap;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ImageUrl {
    pub url: String,
    pub detail: Option<String>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
#[serde(tag = "type")]
pub enum Content {
    #[serde(rename = "image_url")]
    Image { image_url: ImageUrl },
    #[serde(rename = "text")]
    Text { text: String },
}

#[allow(dead_code)]
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ModelInformation {
    pub id: String,
    pub name: String,
    pub description: String,
    pub pricing: HashMap<String, Value>,
    pub context_length: u32,
    pub architecture: HashMap<String, Value>,
    pub top_provider: HashMap<String, Value>,
    pub per_request_limits: Option<HashMap<String, Value>>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Message {
    pub role: String,
    pub content: ContentType,
    pub name: Option<String>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
#[serde(untagged)]
pub enum ContentType {
    String(String),
    List(Vec<Content>),
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Input {
    pub model: String,
    pub user: Option<String>,
    pub messages: Vec<Message>,
    pub temperature: Option<f32>,
    pub top_p: Option<f32>,
    pub presence_penalty: Option<f32>,
    pub frequency_penalty: Option<f32>,
    pub stream: Option<bool>,
}

#[allow(dead_code)]
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Output {
    pub id: String,
    pub object: String,
    pub created: i64,
    pub model: String,
    pub choices: Vec<HashMap<String, Value>>,
    pub usage: HashMap<String, Value>,
}

impl Default for Output {
    fn default() -> Self {
        Self {
            id: "".to_string(),
            object: "chat.completion".to_string(),
            created: chrono::Utc::now().timestamp(),
            model: "".to_string(),
            choices: vec![],
            usage: HashMap::new(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
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
    fn test_model_information_missing_field() {
        let json_data = json!({
            "name": "test_name",
            "description": "test_desc"
        });
        
        let result: Result<ModelInformation, _> = serde_json::from_value(json_data);
        assert!(result.is_err(), "Should fail when required fields are missing");
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
    fn test_output_valid() {
        let output = Output::default();
        assert_eq!(output.object, "chat.completion");
    }
}

