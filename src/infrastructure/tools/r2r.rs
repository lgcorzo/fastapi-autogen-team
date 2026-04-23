use rig::completion::ToolDefinition;
use rig::tool::Tool;
use serde::Deserialize;
use serde_json::json;
use std::env;
use thiserror::Error;

#[derive(Deserialize)]
pub struct R2RArgs {
    pub query: String,
}

#[derive(Debug, Error)]
pub enum R2RError {
    #[error("Environment variable missing: {0}")]
    EnvVarMissing(#[from] env::VarError),
    #[error("Request error: {0}")]
    RequestError(#[from] reqwest::Error),
    #[error("Other error: {0}")]
    Other(String),
}

pub struct R2RTool;

impl Tool for R2RTool {
    const NAME: &'static str = "r2r_search";
    type Error = R2RError;
    type Args = R2RArgs;
    type Output = String;

    async fn definition(&self, _prompt: String) -> ToolDefinition {
        ToolDefinition {
            name: "r2r_search".to_string(),
            description: "Search for general information and documents in the R2R (RAG) system."
                .to_string(),
            parameters: json!({
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query."
                    }
                },
                "required": ["query"]
            }),
        }
    }

    async fn call(&self, args: Self::Args) -> Result<Self::Output, Self::Error> {
        let r2r_url = env::var("R2R_URL").unwrap_or_else(|_| "http://r2r:7272".to_string());
        get_r2r_results(&r2r_url, &args.query)
            .await
            .map_err(|e| R2RError::Other(e.to_string()))
    }
}

pub async fn get_r2r_results(url: &str, query: &str) -> anyhow::Result<String> {
    let user = env::var("R2R_USER")?;
    let pwd = env::var("R2R_PWD")?;

    let client = reqwest::Client::new();

    // 1. Login to get token
    let login_url = format!("{}/v3/users/login", url.trim_end_matches('/'));
    let login_res = client
        .post(&login_url)
        .form(&[("username", &user), ("password", &pwd)])
        .send()
        .await?;

    let login_status = login_res.status();
    let login_body = login_res.text().await?;

    if !login_status.is_success() {
        anyhow::bail!(
            "R2R login failed with status {}. Body: {}",
            login_status,
            login_body
        );
    }

    let login_data: serde_json::Value = serde_json::from_str(&login_body).map_err(|e| {
        anyhow::anyhow!(
            "Failed to decode R2R login response: {}. Body: {}",
            e,
            login_body
        )
    })?;

    let token = login_data["results"]["access_token"]
        .as_str()
        .or_else(|| login_data["results"]["access_token"]["token"].as_str())
        .ok_or_else(|| {
            anyhow::anyhow!(
                "Failed to retrieve access token from R2R. Response was: {}",
                login_data
            )
        })?;

    // 2. Execute search query
    let search_url = format!("{}/v3/retrieval/search", url.trim_end_matches('/'));
    let search_res = client
        .post(&search_url)
        .bearer_auth(token)
        .json(&json!({
            "query": query,
            "stream": false,
            "search_settings": {
                "use_vector_search": true,
                "search_filters": {},
                "search_limit": 3
            }
        }))
        .send()
        .await?;

    let status = search_res.status();
    let body_text = search_res.text().await?;

    if !status.is_success() {
        anyhow::bail!(
            "R2R search query failed with status {}. Body: {}",
            status,
            body_text
        );
    }

    let search_data: serde_json::Value = serde_json::from_str(&body_text).map_err(|e| {
        anyhow::anyhow!(
            "Failed to decode R2R search response: {}. Body: {}",
            e,
            body_text
        )
    })?;

    // 3. Process search results
    let mut combined_results = String::new();
    if let Some(chunks) = search_data["results"]["chunk_search_results"].as_array() {
        for chunk in chunks {
            if let Some(text) = chunk["text"].as_str() {
                if !combined_results.is_empty() {
                    combined_results.push_str("\n\n---\n\n");
                }
                combined_results.push_str(text);
            }
        }
    }

    if combined_results.is_empty() {
        combined_results = "No internal r2r result found".to_string();
    }

    Ok(combined_results)
}
