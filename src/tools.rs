use rig::completion::ToolDefinition;
use rig::tool::Tool;
use serde::{Deserialize, Serialize};
use serde_json::json;
use std::env;
use thiserror::Error;

#[derive(Deserialize)]
pub struct SearchArgs {
    pub query: String,
}

#[derive(Serialize)]
pub struct SearchResult {
    pub r2r: String,
    pub jira: String,
}

#[derive(Debug, Error)]
pub enum SearchError {
    #[error("Environment variable missing: {0}")]
    EnvVarMissing(#[from] env::VarError),
    #[error("Request error: {0}")]
    RequestError(#[from] reqwest::Error),
    #[error("Other error: {0}")]
    Other(String),
}

pub struct SearchTool;

impl Tool for SearchTool {
    const NAME: &'static str = "search";
    type Error = SearchError;
    type Args = SearchArgs;
    type Output = SearchResult;

    async fn definition(&self, _prompt: String) -> ToolDefinition {
        ToolDefinition {
            name: "search".to_string(),
            description: "Search for information in R2R (RAG) and Jira.".to_string(),
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
        let query = args.query;
        tracing::info!("Executing search for: {}", query);

        let r2r_url = env::var("R2R_URL").unwrap_or_else(|_| "http://r2r:7272".to_string());
        let jira_url = env::var("JIRA_INSTANCE_URL").map_err(SearchError::EnvVarMissing)?;

        let r2r_res = get_r2r_results(&r2r_url, &query).await.map_err(|e| {
            tracing::error!("R2R error: {}", e);
            SearchError::Other(e.to_string())
        })?;

        let jira_res = get_jira_results(&jira_url, &query).await.map_err(|e| {
            tracing::error!("Jira error: {}", e);
            SearchError::Other(e.to_string())
        })?;

        Ok(SearchResult {
            r2r: r2r_res,
            jira: jira_res,
        })
    }
}

async fn get_r2r_results(url: &str, query: &str) -> anyhow::Result<String> {
    let user = env::var("R2R_USER")?;
    let pwd = env::var("R2R_PWD")?;

    let client = reqwest::Client::new();
    
    // 1. Login to get token
    let login_url = format!("{}/v2/users/login", url.trim_end_matches('/'));
    let login_res = client.post(&login_url)
        .form(&[("email", &user), ("password", &pwd)])
        .send()
        .await?;
    
    let login_data: serde_json::Value = login_res.json().await?;
    let token = login_data["results"]["access_token"]
        .as_str()
        .ok_or_else(|| anyhow::anyhow!("Failed to retrieve access token from R2R"))?;

    // 2. Execute RAG query
    let rag_url = format!("{}/v2/retrieval/rag", url.trim_end_matches('/'));
    let rag_res = client.post(&rag_url)
        .bearer_auth(token)
        .json(&json!({
            "query": query,
            "use_vector_search": true,
            "search_filters": {},
            "search_limit": 10
        }))
        .send()
        .await?;

    let rag_data: serde_json::Value = rag_res.json().await?;
    
    let search_results = rag_data["results"]["generated_answer"]
        .as_str()
        .unwrap_or("No internal r2r result found")
        .to_string();

    Ok(search_results)
}

async fn get_jira_results(url: &str, query: &str) -> anyhow::Result<String> {
    let user = env::var("JIRA_USERNAME")?;
    let token = env::var("JIRA_API_TOKEN")?;

    let client = reqwest::Client::new();
    
    // JQL query
    let sanitized_query = query.replace('\\', "\\\\").replace('"', "\\\"");
    let jql = format!("summary ~ \"{}\" OR description ~ \"{}\"", sanitized_query, sanitized_query);
    
    let search_url = format!("{}/rest/api/2/search", url.trim_end_matches('/'));
    let res = client.get(&search_url)
        .basic_auth(&user, Some(&token))
        .query(&[("jql", &jql)])
        .send()
        .await?;

    let data: serde_json::Value = res.json().await?;
    let issues = data["issues"].as_array();
    
    match issues {
        Some(list) if !list.is_empty() => {
            let res_list: Vec<String> = list.iter().map(|issue| {
                let key = issue["key"].as_str().unwrap_or("UNKNOWN");
                let summary = issue["fields"]["summary"].as_str().unwrap_or("No summary");
                format!("[{}] {}", key, summary)
            }).collect();
            Ok(res_list.join("\n"))
        },
        _ => Ok("No se encontraron resultados en Jira.".to_string()),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use mockito::Server;

    #[tokio::test]
    async fn test_get_r2r_results_success() {
        let mut server = Server::new_async().await;
        let url = server.url();

        env::set_var("R2R_USER", "test_user");
        env::set_var("R2R_PWD", "test_pwd");

        let _m_login = server.mock("POST", "/v2/users/login")
            .with_status(200)
            .with_header("content-type", "application/json")
            .with_body(r#"{"results": {"access_token": "mock_token"}}"#)
            .create_async().await;

        let _m_rag = server.mock("POST", "/v2/retrieval/rag")
            .with_status(200)
            .with_header("content-type", "application/json")
            .with_body(r#"{"results": {"generated_answer": "Mocked answer"}}"#)
            .create_async().await;

        let res = get_r2r_results(&url, "test query").await.unwrap();
        assert_eq!(res, "Mocked answer");
    }

    #[tokio::test]
    async fn test_get_jira_results_success() {
        let mut server = Server::new_async().await;
        let url = server.url();

        env::set_var("JIRA_USERNAME", "test_user");
        env::set_var("JIRA_API_TOKEN", "test_token");

        let _m = server.mock("GET", "/rest/api/2/search")
            .match_query(mockito::Matcher::Any)
            .with_status(200)
            .with_header("content-type", "application/json")
            .with_body(r#"{"issues": [{"key": "PROJ-1", "fields": {"summary": "Issue 1"}}]}"#)
            .create_async().await;

        let res = get_jira_results(&url, "test query").await.unwrap();
        assert!(res.contains("[PROJ-1] Issue 1"));
    }

    #[tokio::test]
    async fn test_get_jira_results_no_results() {
        let mut server = Server::new_async().await;
        let url = server.url();

        env::set_var("JIRA_USERNAME", "test_user");
        env::set_var("JIRA_API_TOKEN", "test_token");

        let _m = server.mock("GET", "/rest/api/2/search")
            .match_query(mockito::Matcher::Any)
            .with_status(200)
            .with_header("content-type", "application/json")
            .with_body(r#"{"issues": []}"#)
            .create_async().await;

        let res = get_jira_results(&url, "empty").await.unwrap();
        assert_eq!(res, "No se encontraron resultados en Jira.");
    }
}

