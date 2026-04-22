use mockito::Server;
use rust_agent_team::infrastructure::tools::confluence::get_confluence_results;
use std::env;

#[tokio::test]
async fn test_get_confluence_results_success() {
    let mut server = Server::new_async().await;
    let url = server.url();

    env::set_var("JIRA_USERNAME", "test_user");
    env::set_var("JIRA_API_TOKEN", "test_token");

    let _m = server
        .mock("GET", "/wiki/rest/api/content/search")
        .match_query(mockito::Matcher::Any)
        .with_status(200)
        .with_header("content-type", "application/json")
        .with_body(
            r#"{"results": [{"title": "Page 1", "_links": {"webui": "/display/SPACE/Page+1"}}]}"#,
        )
        .create_async()
        .await;

    let res = get_confluence_results(&url, "test query").await.unwrap();
    assert!(res.contains("- Page 1: http"));
}

#[tokio::test]
async fn test_get_confluence_results_no_results() {
    let mut server = Server::new_async().await;
    let url = server.url();

    env::set_var("JIRA_USERNAME", "test_user");
    env::set_var("JIRA_API_TOKEN", "test_token");

    let _m = server
        .mock("GET", "/wiki/rest/api/content/search")
        .match_query(mockito::Matcher::Any)
        .with_status(200)
        .with_header("content-type", "application/json")
        .with_body(r#"{"results": []}"#)
        .create_async()
        .await;

    let res = get_confluence_results(&url, "test query").await.unwrap();
    assert!(res.contains("No se encontraron resultados"));
}
