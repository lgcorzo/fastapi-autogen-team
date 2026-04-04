use fastapi_autogen_team::infrastructure::tools::r2r::get_r2r_results;
use mockito::Server;
use std::env;

#[tokio::test]
async fn test_get_r2r_results_success() {
    let mut server = Server::new_async().await;
    let url = server.url();

    env::set_var("R2R_USER", "test_user");
    env::set_var("R2R_PWD", "test_pwd");

    let _m_login = server
        .mock("POST", "/v3/users/login")
        .with_status(200)
        .with_header("content-type", "application/json")
        .with_body(r#"{"results": {"access_token": {"token": "mock_token", "token_type": "bearer"}, "refresh_token": {"token": "mock_refresh", "token_type": "bearer"}}}"#)
        .create_async()
        .await;

    let _m_rag = server
        .mock("POST", "/v3/retrieval/search")
        .with_status(200)
        .with_header("content-type", "application/json")
        .with_body(r#"{"results": {"chunk_search_results": [{"text": "Mocked answer"}]}}"#)
        .create_async()
        .await;

    let res = get_r2r_results(&url, "test query").await.unwrap();
    assert_eq!(res, "Mocked answer");
}
