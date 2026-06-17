use rig::completion::ToolDefinition;
use rig::tool::Tool;
use serde::Deserialize;
use serde_json::json;
use std::env;
use thiserror::Error;

#[derive(Deserialize)]
pub struct ConfluenceArgs {
    pub query: String,
}

#[derive(Debug, Error)]
pub enum ConfluenceError {
    #[error("Environment variable missing: {0}")]
    EnvVarMissing(#[from] env::VarError),
    #[error("Request error: {0}")]
    RequestError(#[from] reqwest::Error),
    #[error("Other error: {0}")]
    Other(String),
}

pub struct ConfluenceTool;

impl Tool for ConfluenceTool {
    const NAME: &'static str = "confluence_search";
    type Error = ConfluenceError;
    type Args = ConfluenceArgs;
    type Output = String;

    async fn definition(&self, _prompt: String) -> ToolDefinition {
        ToolDefinition {
            name: "confluence_search".to_string(),
            description: "Search for documentation and pages in Confluence.".to_string(),
            parameters: json!({
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search keywords or phrase to look for. Provide ONLY the text to search for, DO NOT use CQL clauses like 'space:' or 'type:'."
                    }
                },
                "required": ["query"]
            }),
        }
    }

    async fn call(&self, args: Self::Args) -> Result<Self::Output, Self::Error> {
        let jira_url = env::var("JIRA_INSTANCE_URL").map_err(ConfluenceError::EnvVarMissing)?;
        get_confluence_results(&jira_url, &args.query)
            .await
            .map_err(|e| ConfluenceError::Other(e.to_string()))
    }
}

pub async fn get_confluence_results(url: &str, query: &str) -> anyhow::Result<String> {
    let user = env::var("JIRA_USERNAME")?;
    let token = env::var("JIRA_API_TOKEN")?;

    let client = reqwest::Client::new();

    // CQL query
    let sanitized_query = query.replace('\\', "\\\\").replace('"', "\\\"");
    let cql = format!(
        "text ~ \"{}\" OR title ~ \"{}\"",
        sanitized_query, sanitized_query
    );

    let base_url = url.trim_end_matches('/');
    let search_url = if base_url.ends_with("/wiki") {
        format!("{}/rest/api/content/search", base_url)
    } else {
        format!("{}/wiki/rest/api/content/search", base_url)
    };

    let res = client
        .get(&search_url)
        .basic_auth(&user, Some(&token))
        .query(&[("cql", &cql)])
        .send()
        .await?;

    let data: serde_json::Value = res.json().await?;
    let results = data["results"].as_array();

    match results {
        Some(list) if !list.is_empty() => {
            let res_list: Vec<String> = list
                .iter()
                .map(|item| {
                    let title = item["title"].as_str().unwrap_or("No title");
                    let webui = item["_links"]["webui"].as_str().unwrap_or("");
                    let full_url = format!("{}{}", base_url, webui);
                    format!("- {}: {}", title, full_url)
                })
                .collect();
            Ok(res_list.join("\n"))
        }
        _ => Ok("No se encontraron resultados en Confluence.".to_string()),
    }
}
