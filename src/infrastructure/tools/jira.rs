use rig::completion::ToolDefinition;
use rig::tool::Tool;
use serde::Deserialize;
use serde_json::json;
use std::env;
use thiserror::Error;

#[derive(Deserialize)]
pub struct JiraArgs {
    pub query: String,
}

#[derive(Debug, Error)]
pub enum JiraError {
    #[error("Environment variable missing: {0}")]
    EnvVarMissing(#[from] env::VarError),
    #[error("Request error: {0}")]
    RequestError(#[from] reqwest::Error),
    #[error("Other error: {0}")]
    Other(String),
}

pub struct JiraTool;

impl Tool for JiraTool {
    const NAME: &'static str = "jira_search";
    type Error = JiraError;
    type Args = JiraArgs;
    type Output = String;

    async fn definition(&self, _prompt: String) -> ToolDefinition {
        ToolDefinition {
            name: "jira_search".to_string(),
            description: "Search for tasks and issues in Jira.".to_string(),
            parameters: json!({
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query (JQL compatible keywords)."
                    }
                },
                "required": ["query"]
            }),
        }
    }

    async fn call(&self, args: Self::Args) -> Result<Self::Output, Self::Error> {
        let jira_url = env::var("JIRA_INSTANCE_URL").map_err(JiraError::EnvVarMissing)?;
        get_jira_results(&jira_url, &args.query)
            .await
            .map_err(|e| JiraError::Other(e.to_string()))
    }
}

pub async fn get_jira_results(url: &str, query: &str) -> anyhow::Result<String> {
    let user = env::var("JIRA_USERNAME")?;
    let token = env::var("JIRA_API_TOKEN")?;

    let client = reqwest::Client::new();

    // JQL query
    let sanitized_query = query.replace('\\', "\\\\").replace('"', "\\\"");
    let trimmed_query = sanitized_query.trim();

    let jql = if trimmed_query
        .chars()
        .all(|c| c.is_alphanumeric() || c == '-')
        && trimmed_query.contains('-')
    {
        format!(
            "key = \"{}\" OR summary ~ \"{}\" OR description ~ \"{}\"",
            trimmed_query, sanitized_query, sanitized_query
        )
    } else {
        format!(
            "summary ~ \"{}\" OR description ~ \"{}\"",
            sanitized_query, sanitized_query
        )
    };

    let search_url = format!("{}/rest/api/3/search/jql", url.trim_end_matches('/'));
    let res = client
        .get(&search_url)
        .basic_auth(&user, Some(&token))
        .query(&[("jql", jql.as_str()), ("fields", "summary,key")])
        .send()
        .await?;

    let data: serde_json::Value = res.json().await?;
    let issues = data["issues"].as_array();

    match issues {
        Some(list) if !list.is_empty() => {
            let res_list: Vec<String> = list
                .iter()
                .map(|issue| {
                    let key = issue["key"].as_str().unwrap_or("UNKNOWN");
                    let summary = issue["fields"]["summary"].as_str().unwrap_or("No summary");
                    format!("[{}] {}", key, summary)
                })
                .collect();
            Ok(res_list.join("\n"))
        }
        _ => Ok("No se encontraron resultados en Jira.".to_string()),
    }
}
