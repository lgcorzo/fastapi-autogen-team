use axum::{
    body::Body,
    http::{self, Request, StatusCode},
};
use fastapi_autogen_team::application::dtos::{ContentType, Input, Message};
use fastapi_autogen_team::domain::agent::team::AgentTeam;
use fastapi_autogen_team::{create_app, AppState};
use http_body_util::BodyExt;
use mockito::Server;
use serde_json::Value;
use std::env;
use std::sync::Arc;
use tower::ServiceExt;

#[tokio::test]
async fn test_docs_redirect() {
    let team = AgentTeam::new_mock();
    let state = Arc::new(AppState { team });
    let app = create_app(state);

    let response = app
        .oneshot(
            Request::builder()
                .uri("/autogen")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();

    assert_eq!(response.status(), StatusCode::SEE_OTHER);
    assert_eq!(
        response.headers().get("location").unwrap(),
        "https://autogen-team.com/docs"
    );
}

#[tokio::test]
async fn test_get_models() {
    let team = AgentTeam::new_mock();
    let state = Arc::new(AppState { team });
    let app = create_app(state);

    let response = app
        .oneshot(
            Request::builder()
                .uri("/autogen/api/v1beta/models")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();

    assert_eq!(response.status(), StatusCode::OK);

    let body = response.into_body().collect().await.unwrap().to_bytes();
    let body: Value = serde_json::from_slice(&body).unwrap();

    let data = body["data"].as_array().unwrap();
    assert!(data.iter().any(|m| m["id"] == "minimax-m2.7:cloud"));
}

#[tokio::test]
async fn test_chat_completions_route() {
    let mut server = Server::new_async().await;
    let url = server.url();

    env::set_var("LITELLM_API_KEY", "test_key");
    env::set_var("LITELLM_BASE_URL", &url);
    env::set_var("R2R_URL", &url);
    env::set_var("JIRA_INSTANCE_URL", &url);
    env::set_var("R2R_USER", "test_user");
    env::set_var("R2R_PWD", "test_pwd");
    env::set_var("JIRA_USERNAME", "test_user");
    env::set_var("JIRA_API_TOKEN", "test_token");

    // 1. Planner Agent Call
    let _m1 = server.mock("POST", "/chat/completions")
        .with_status(200)
        .with_header("content-type", "application/json")
        .with_body(r#"{
            "id": "p1", "object": "chat.completion", "created": 12345, "model": "test",
            "choices":[{"message":{"content":"search query 1","role":"assistant"},"index":0,"finish_reason":"stop"}],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        }"#)
        .create_async().await;

    // 2. RAG Searcher Call (Trigger Tool)
    let _m2 = server
        .mock("POST", "/chat/completions")
        .with_status(200)
        .with_header("content-type", "application/json")
        .with_body(
            r#"{
            "id": "s1", "object": "chat.completion", "created": 12345, "model": "test",
            "choices": [{
                "message": {
                    "role": "assistant",
                    "tool_calls": [{
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "search",
                            "arguments": "{\"query\": \"search query 1\"}"
                        }
                    }]
                },
                "index": 0,
                "finish_reason": "tool_calls"
            }],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        }"#,
        )
        .create_async()
        .await;

    // 3. R2R Mocks
    let _m_r2r_login = server
        .mock("POST", "/v3/users/login")
        .with_status(200)
        .with_header("content-type", "application/json")
        .with_body(r#"{"results": {"access_token": {"token": "mock_token"}}}"#)
        .create_async()
        .await;

    let _m_r2r_search = server
        .mock("POST", "/v3/retrieval/search")
        .with_status(200)
        .with_header("content-type", "application/json")
        .with_body(
            r#"{"results": {"chunk_search_results": [{"text": "Mocked R2R search results"}]}}"#,
        )
        .create_async()
        .await;

    // 4. Jira Mock
    let _m_jira = server
        .mock("GET", "/rest/api/2/search")
        .match_query(mockito::Matcher::Any)
        .with_status(200)
        .with_header("content-type", "application/json")
        .with_body(r#"{"issues": [{"key": "PROJ-1", "fields": {"summary": "Mocked Jira Issue"}}]}"#)
        .create_async()
        .await;

    // 5. RAG Searcher Call (Response after tool)
    let _m3 = server.mock("POST", "/chat/completions")
        .with_status(200)
        .with_header("content-type", "application/json")
        .with_body(r#"{
            "id": "s2", "object": "chat.completion", "created": 12345, "model": "test",
            "choices":[{"message":{"content":"Search completed successfully. Here is the info...","role":"assistant"},"index":0,"finish_reason":"stop"}],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        }"#)
        .create_async().await;

    // 6. QA Agent Call
    let _m4 = server.mock("POST", "/chat/completions")
        .with_status(200)
        .with_header("content-type", "application/json")
        .with_body(r#"{
            "id": "q1", "object": "chat.completion", "created": 12345, "model": "test",
            "choices":[{"message":{"content":"Final synthesized response TERMINATE","role":"assistant"},"index":0,"finish_reason":"stop"}],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        }"#)
        .create_async().await;

    let team = AgentTeam::new_test(&url);
    let state = Arc::new(AppState { team });
    let app = create_app(state);

    let input = Input {
        model: "test".to_string(),
        user: None,
        messages: vec![Message {
            role: "user".to_string(),
            content: ContentType::String("Hello".to_string()),
            name: None,
        }],
        temperature: None,
        top_p: None,
        presence_penalty: None,
        frequency_penalty: None,
        stream: Some(false),
    };

    let response = app
        .oneshot(
            Request::builder()
                .method(http::Method::POST)
                .uri("/autogen/api/v1beta/chat/completions")
                .header(http::header::CONTENT_TYPE, "application/json")
                .body(Body::from(serde_json::to_vec(&input).unwrap()))
                .unwrap(),
        )
        .await
        .unwrap();

    assert_eq!(response.status(), StatusCode::OK);

    let body_bytes = response.into_body().collect().await.unwrap().to_bytes();
    let body_str = String::from_utf8_lossy(&body_bytes);
    assert!(
        body_str.contains("Final synthesized response"),
        "Body does not contain expected response: {}",
        body_str
    );
}
