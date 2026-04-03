use std::env;

pub async fn get_jira_results(url: &str, query: &str) -> anyhow::Result<String> {
    let user = env::var("JIRA_USERNAME")?;
    let token = env::var("JIRA_API_TOKEN")?;

    let client = reqwest::Client::new();

    // JQL query
    let sanitized_query = query.replace('\\', "\\\\").replace('"', "\\\"");
    let jql = format!(
        "summary ~ \"{}\" OR description ~ \"{}\"",
        sanitized_query, sanitized_query
    );

    let search_url = format!("{}/rest/api/2/search", url.trim_end_matches('/'));
    let res = client
        .get(&search_url)
        .basic_auth(&user, Some(&token))
        .query(&[("jql", &jql)])
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
