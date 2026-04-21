use mockito::Server;
use rust_agent_team::infrastructure::tools::jira::get_jira_results;
use std::env;

#[tokio::test]
async fn test_get_jira_results_success() {
    let mut server = Server::new_async().await;
    let url = server.url();

    env::set_var("JIRA_USERNAME", "test_user");
    env::set_var("JIRA_API_TOKEN", "test_token");

    let _m = server
        .mock("GET", "/rest/api/2/search")
        .match_query(mockito::Matcher::Any)
        .with_status(200)
        .with_header("content-type", "application/json")
        .with_body(r#"{"issues": [{"key": "PROJ-1", "fields": {"summary": "Issue 1"}}]}"#)
        .create_async()
        .await;

    let res = get_jira_results(&url, "test query").await.unwrap();
    assert!(res.contains("[PROJ-1] Issue 1"));
}
