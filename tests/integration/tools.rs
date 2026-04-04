use fastapi_autogen_team::infrastructure::tools::jira::get_jira_results;
use fastapi_autogen_team::infrastructure::tools::r2r::get_r2r_results;
use mockito::Server;
use std::env;

#[tokio::test]
async fn test_get_r2r_results_success() {
    let mut server = Server::new_async().await;
    let url = server.url();

    let _m_login = server.mock("POST", "/v3/users/login")
        .with_status(200)
        .with_header("content-type", "application/json")
        .with_body(r#"{"results": {"access_token": {"token": "test_token"}}}"#)
        .create_async()
        .await;

    let _m_rag = server.mock("POST", "/v3/retrieval/rag")
        .with_status(200)
        .with_header("content-type", "application/json")
        .with_body(r#"{"results": {"generated_answer": "Test RAG Answer"}}"#)
        .create_async()
        .await;

    env::set_var("R2R_USER", "test");
    env::set_var("R2R_PWD", "test");

    let result = get_r2r_results(&url, "test query").await;
    assert!(result.is_ok());
    assert_eq!(result.unwrap(), "Test RAG Answer");
}

#[tokio::test]
async fn test_get_jira_results_success() {
    let mut server = Server::new_async().await;
    let url = server.url();

    let _m_jira = server.mock("GET", "/rest/api/2/search")
        .match_query(mockito::Matcher::Any)
        .with_status(200)
        .with_header("content-type", "application/json")
        .with_body(r#"{
            "issues": [
                {
                    "key": "TEST-1",
                    "fields": {
                        "summary": "Test Summary"
                    }
                }
            ]
        }"#)
        .create_async()
        .await;

    env::set_var("JIRA_USERNAME", "test");
    env::set_var("JIRA_API_TOKEN", "test");

    let result = get_jira_results(&url, "test query").await;
    assert!(result.is_ok());
    assert_eq!(result.unwrap(), "[TEST-1] Test Summary");
}

#[tokio::test]
async fn test_get_jira_results_no_issues() {
    let mut server = Server::new_async().await;
    let url = server.url();

    let _m_jira = server.mock("GET", "/rest/api/2/search")
        .match_query(mockito::Matcher::Any)
        .with_status(200)
        .with_header("content-type", "application/json")
        .with_body(r#"{"issues": []}"#)
        .create_async()
        .await;

    env::set_var("JIRA_USERNAME", "test");
    env::set_var("JIRA_API_TOKEN", "test");

    let result = get_jira_results(&url, "test query").await;
    assert!(result.is_ok());
    assert_eq!(result.unwrap(), "No se encontraron resultados en Jira.");
}
