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
