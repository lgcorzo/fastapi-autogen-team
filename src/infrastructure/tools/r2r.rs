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
}
