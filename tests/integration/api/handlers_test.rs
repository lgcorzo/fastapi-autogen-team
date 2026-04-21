use axum::{
    extract::State,
    http::{HeaderMap, StatusCode},
    response::IntoResponse,
};
use mockito::Server;
use rust_agent_team::application::dtos::{ContentType, Input, Message};
use rust_agent_team::domain::agent::team::AgentTeam;
use rust_agent_team::interface::http::handlers::{docs_redirect, get_models, route_query};
use rust_agent_team::interface::http::routes::AppState;
use rust_agent_team::interface::http::validation::ValidatedJson;
use std::sync::Arc;

#[tokio::test]
async fn test_docs_redirect() {
    let res = docs_redirect().await;
    let response = res.into_response();
    assert_eq!(response.status(), StatusCode::SEE_OTHER);
    assert_eq!(
        response.headers().get("Location").unwrap(),
        "https://agent-team.com/docs"
    );
}

#[tokio::test]
async fn test_get_models() {
    let res = get_models().await;
    let response = res.into_response();
    assert_eq!(response.status(), StatusCode::OK);
}

#[tokio::test]
async fn test_route_query_no_stream() {
    let mut server = Server::new_async().await;
    let url = server.url();

    // Mock the planner call
    let _m1 = server.mock("POST", "/chat/completions")
        .with_status(200)
        .with_header("content-type", "application/json")
        .with_body(r#"{
            "id": "p1", "object": "chat.completion", "created": 12345, "model": "test",
            "choices":[{"message":{"content":"search query 1\nsearch query 2","role":"assistant"},"index":0,"finish_reason":"stop"}],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        }"#)
        .create_async().await;

    // Mock searcher calls (2 queries)
    let _m2 = server.mock("POST", "/chat/completions")
        .with_status(200)
        .with_header("content-type", "application/json")
        .with_body(r#"{
            "id": "s1", "object": "chat.completion", "created": 12345, "model": "test",
            "choices":[{"message":{"content":"Search results part 1","role":"assistant"},"index":0,"finish_reason":"stop"}],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        }"#)
        .create_async().await;

    let _m3 = server.mock("POST", "/chat/completions")
        .with_status(200)
        .with_header("content-type", "application/json")
        .with_body(r#"{
            "id": "s2", "object": "chat.completion", "created": 12345, "model": "test",
            "choices":[{"message":{"content":"Search results part 2","role":"assistant"},"index":0,"finish_reason":"stop"}],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        }"#)
        .create_async().await;

    // Mock QA call
    let _m4 = server.mock("POST", "/chat/completions")
        .with_status(200)
        .with_header("content-type", "application/json")
        .with_body(r#"{
            "id": "q1", "object": "chat.completion", "created": 12345, "model": "test",
            "choices":[{"message":{"content":"Final response TERMINATE","role":"assistant"},"index":0,"finish_reason":"stop"}],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        }"#)
        .create_async().await;

    let state = Arc::new(AppState {
        team: AgentTeam::new_test(&url),
    });
    let request = Input {
        model: "test".to_string(),
        messages: vec![Message {
            role: "user".to_string(),
            content: ContentType::String("hello".to_string()),
            name: None,
        }],
        stream: Some(false),
        temperature: None,
        user: None,
        top_p: None,
        presence_penalty: None,
        frequency_penalty: None,
    };

    let mut headers = HeaderMap::new();
    headers.insert("authorization", "Bearer test".parse().unwrap());

    let res = route_query(State(state), headers, ValidatedJson(request)).await;
    let response = res.into_response();
    assert_eq!(response.status(), StatusCode::OK);
}
