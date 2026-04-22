use crate::infrastructure::tools::confluence::get_confluence_results;
use crate::infrastructure::tools::jira::get_jira_results;
use crate::infrastructure::tools::r2r::get_r2r_results;
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
    pub confluence: String,
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
            description: "Search for information in R2R (RAG), Jira, and Confluence.".to_string(),
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
            SearchError::Other("An internal error occurred in R2R search".to_string())
        })?;

        let jira_res = get_jira_results(&jira_url, &query).await.map_err(|e| {
            tracing::error!("Jira error: {}", e);
            SearchError::Other("An internal error occurred in Jira search".to_string())
        })?;

        let confluence_res = get_confluence_results(&jira_url, &query)
            .await
            .map_err(|e| {
                tracing::error!("Confluence error: {}", e);
                SearchError::Other("An internal error occurred in Confluence search".to_string())
            })?;

        Ok(SearchResult {
            r2r: r2r_res,
            jira: jira_res,
            confluence: confluence_res,
        })
    }
}
