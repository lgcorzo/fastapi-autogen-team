use std::env;

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
