use std::env;
use serde_json::json;

pub async fn get_r2r_results(url: &str, query: &str) -> anyhow::Result<String> {
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


