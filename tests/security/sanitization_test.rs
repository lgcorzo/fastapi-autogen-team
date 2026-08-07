use axum::{
    body::Body,
    http::{Request, StatusCode},
};
use http_body_util::BodyExt;
use rust_agent_team::domain::agent::team::AgentTeam;
use rust_agent_team::{create_app, AppState};
use serde_json::json;
use std::sync::Arc;
use tower::ServiceExt;

#[tokio::test]
async fn test_large_payload_rejection() {
    let state = Arc::new(AppState {
        team: AgentTeam::new_mock(),
    });
    let app = create_app(state);

    // Create a very large payload (e.g., 10MB)
    let large_string = "A".repeat(10 * 1024 * 1024);
    let payload = json!({
        "model": "test",
        "messages": [{"role": "user", "content": large_string}]
    });

    let response = app
        .oneshot(
            Request::builder()
                .method("POST")
                .uri("/agent/api/v1beta/chat/completions")
                .header("Content-Type", "application/json")
                .body(Body::from(payload.to_string()))
                .unwrap(),
        )
        .await
        .unwrap();

    // Standard Axum/Tower-HTTP limit is usually around 2MB or similar by default if configured
    assert_eq!(response.status(), StatusCode::PAYLOAD_TOO_LARGE);

    let body_bytes = response.into_body().collect().await.unwrap().to_bytes();
    let body_json: serde_json::Value = serde_json::from_slice(&body_bytes).unwrap();
    assert_eq!(
        body_json["details"].as_str().unwrap(),
        "The request payload exceeds the maximum allowed size."
    );
}

#[tokio::test]
async fn test_invalid_json_rejection() {
    let state = Arc::new(AppState {
        team: AgentTeam::new_mock(),
    });
    let app = create_app(state);

    let response = app
        .oneshot(
            Request::builder()
                .method("POST")
                .uri("/agent/api/v1beta/chat/completions")
                .header("Content-Type", "application/json")
                .body(Body::from("{ invalid json }"))
                .unwrap(),
        )
        .await
        .unwrap();

    assert_eq!(response.status(), StatusCode::UNPROCESSABLE_ENTITY); // Axum default for bad JSON

    let body_bytes = response.into_body().collect().await.unwrap().to_bytes();
    let body_json: serde_json::Value = serde_json::from_slice(&body_bytes).unwrap();
    assert_eq!(
        body_json["details"].as_str().unwrap(),
        "Failed to parse request body as JSON or invalid payload structure."
    );
}

#[tokio::test]
async fn test_empty_messages_validation() {
    let state = Arc::new(AppState {
        team: AgentTeam::new_mock(),
    });
    let app = create_app(state);

    let payload = json!({
        "model": "test",
        "messages": []
    });

    let response = app
        .oneshot(
            Request::builder()
                .method("POST")
                .uri("/agent/api/v1beta/chat/completions")
                .header("Content-Type", "application/json")
                .body(Body::from(payload.to_string()))
                .unwrap(),
        )
        .await
        .unwrap();

    // Depending on validator, this should be an error
    assert_eq!(response.status(), StatusCode::UNPROCESSABLE_ENTITY);
}

#[tokio::test]
async fn test_cors_malformed_origins_no_panic() {
    std::env::set_var("ALLOWED_ORIGINS", "invalid origin, , http://localhost:3000");
    let state = Arc::new(AppState {
        team: AgentTeam::new_mock(),
    });
    // This should not panic
    let _app = create_app(state);
    std::env::remove_var("ALLOWED_ORIGINS");
}

#[tokio::test]
async fn test_cors_empty_origins_no_panic() {
    std::env::set_var("ALLOWED_ORIGINS", ", , ");
    let state = Arc::new(AppState {
        team: AgentTeam::new_mock(),
    });
    // This should not panic
    let _app = create_app(state);
    std::env::remove_var("ALLOWED_ORIGINS");
}
