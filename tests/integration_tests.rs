use axum::{
    body::Body,
    http::{self, Request, StatusCode},
};
use fastapi_autogen_team::{create_app, AppState};
use fastapi_autogen_team::domain::agent::team::AgentTeam;
use fastapi_autogen_team::application::dtos::{Input, Message, ContentType};
use http_body_util::BodyExt;
use serde_json::{json, Value};
use std::sync::Arc;
use tower::ServiceExt;
use mockito::Server;
use std::env;

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

    assert_eq!(response.status(), StatusCode::TEMPORARY_REDIRECT);
    assert_eq!(response.headers().get("location").unwrap(), "/autogen/api/v1beta/docs");
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
    assert_eq!(body["data"]["name"], "internal-gpt");
}

#[tokio::test]
async fn test_chat_completions_route() {
    let mut server = Server::new_async().await;
    let url = server.url();

    env::set_var("LITELLM_API_KEY", "test_key");
    env::set_var("LITELLM_BASE_URL", &url);

    // Mock the 3 stages in sequence
    let _m1 = server.mock("POST", mockito::Matcher::Any)
        .with_status(200)
        .with_body(json!({
            "id": "mock-1",
            "object": "response",
            "created_at": 12345,
            "status": "completed",
            "model": "gpt-4o",
            "output": [{
                "type": "message",
                "id": "msg-123",
                "role": "assistant",
                "status": "completed",
                "content": [{"type": "output_text", "text": "query1"}]
            }]
        }).to_string())
        .create_async().await;

    let _m2 = server.mock("POST", mockito::Matcher::Any)
        .with_status(200)
        .with_body(json!({
            "id": "mock-2",
            "object": "response",
            "created_at": 12346,
            "status": "completed",
            "model": "gpt-4o",
            "output": [{
                "type": "message",
                "id": "msg-456",
                "role": "assistant",
                "status": "completed",
                "content": [{"type": "output_text", "text": "search result"}]
            }]
        }).to_string())
        .create_async().await;

    let _m3 = server.mock("POST", mockito::Matcher::Any)
        .with_status(200)
        .with_body(json!({
            "id": "mock-3",
            "object": "response",
            "created_at": 12347,
            "status": "completed",
            "model": "gpt-4o",
            "output": [{
                "type": "message",
                "id": "msg-789",
                "role": "assistant",
                "status": "completed",
                "content": [{"type": "output_text", "text": "final synthesis TERMINATE"}]
            }]
        }).to_string())
        .create_async().await;

    let team = AgentTeam::new().await.unwrap();
    let state = Arc::new(AppState { team });
    let app = create_app(state);

    let input = Input {
        model: "test".to_string(),
        user: None,
        messages: vec![Message { role: "user".to_string(), content: ContentType::String("Hello".to_string()), name: None }],
        temperature: None,
        top_p: None,
        presence_penalty: None,
        frequency_penalty: None,
        stream: None,
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
}
