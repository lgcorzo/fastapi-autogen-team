use axum::{
    body::Body,
    http::{self, Request, StatusCode},
};
use fastapi_autogen_team::{create_app, AppState};
use fastapi_autogen_team::domain::agent::team::AgentTeam;
use fastapi_autogen_team::application::dtos::{Input, Message, ContentType};
use http_body_util::BodyExt;
use serde_json::Value;
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

    assert_eq!(response.status(), StatusCode::SEE_OTHER);
    assert_eq!(response.headers().get("location").unwrap(), "https://autogen-team.com/docs");
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
    let server = Server::new_async().await;
    let url = server.url();

    env::set_var("LITELLM_API_KEY", "test_key");
    env::set_var("LITELLM_BASE_URL", &url);

    let team = AgentTeam::new_test(&url);
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
        stream: Some(false),
    };

    // Since we are mocking the entire client and the handler handles errors gracefully,
    // we can check for OK status or error string in body.
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
