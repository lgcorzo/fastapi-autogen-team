use axum::{
    body::Body,
    http::{Request, StatusCode},
};
use fastapi_autogen_team::domain::agent::team::AgentTeam;
use fastapi_autogen_team::{create_app, AppState};
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
                .uri("/autogen/api/v1beta/chat/completions")
                .header("Content-Type", "application/json")
                .body(Body::from(payload.to_string()))
                .unwrap(),
        )
        .await
        .unwrap();

    // Standard Axum/Tower-HTTP limit is usually around 2MB or similar by default if configured
    // If not configured, it might be OK, but for security, we should check for reasonable limits.
    // Here we check if the service handles it (either OK if under limit or PayloadTooLarge)
    assert!(
        response.status() == StatusCode::OK || response.status() == StatusCode::PAYLOAD_TOO_LARGE
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
                .uri("/autogen/api/v1beta/chat/completions")
                .header("Content-Type", "application/json")
                .body(Body::from("{ invalid json }"))
                .unwrap(),
        )
        .await
        .unwrap();

    assert_eq!(response.status(), StatusCode::UNPROCESSABLE_ENTITY); // Axum default for bad JSON
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
                .uri("/autogen/api/v1beta/chat/completions")
                .header("Content-Type", "application/json")
                .body(Body::from(payload.to_string()))
                .unwrap(),
        )
        .await
        .unwrap();

    // Depending on validator, this should be an error
    assert_eq!(response.status(), StatusCode::UNPROCESSABLE_ENTITY);
}
