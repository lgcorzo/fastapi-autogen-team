use axum::{
    body::Body,
    http::{Request, StatusCode},
};
use tower::ServiceExt;
use std::sync::Arc;
use fastapi_autogen_team::{create_app, AppState};
use fastapi_autogen_team::domain::agent::team::AgentTeam;
use serde_json::json;

#[tokio::test]
async fn test_security_headers_present() {
    let state = Arc::new(AppState {
        team: AgentTeam::new_mock(),
    });
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

    assert_eq!(response.headers().get("x-content-type-options").unwrap(), "nosniff");
    assert_eq!(response.headers().get("x-frame-options").unwrap(), "DENY");
    assert!(response.headers().get("strict-transport-security").unwrap().to_str().unwrap().contains("max-age=31536000"));
}

#[tokio::test]
async fn test_cors_specific_origins() {
    std::env::set_var("ALLOWED_ORIGINS", "https://good.com,https://another.com");
    let state = Arc::new(AppState {
        team: AgentTeam::new_mock(),
    });
    let app = create_app(state);

    // Good origin
    let response_good = app.clone()
        .oneshot(
            Request::builder()
                .method("OPTIONS")
                .uri("/autogen/api/v1beta/models")
                .header("Origin", "https://good.com")
                .header("Access-Control-Request-Method", "GET")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();

    assert_eq!(response_good.status(), StatusCode::OK);
    assert_eq!(response_good.headers().get("access-control-allow-origin").unwrap(), "https://good.com");

    // Bad origin
    let response_bad = app
        .oneshot(
            Request::builder()
                .method("OPTIONS")
                .uri("/autogen/api/v1beta/models")
                .header("Origin", "https://evil.com")
                .header("Access-Control-Request-Method", "GET")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();

    assert_eq!(response_bad.status(), StatusCode::OK);
    assert!(response_bad.headers().get("access-control-allow-origin").is_none());
}

#[tokio::test]
async fn test_header_injection_sanitization() {
    let state = Arc::new(AppState {
        team: AgentTeam::new_mock(),
    });
    let app = create_app(state);

    // Malicious header with CRLF injection
    let malicious_header = "user\r\nInjected-Header: malicious";

    let payload = json!({
        "model": "test",
        "messages": [{"role": "user", "content": "Hello"}]
    });

    let res = Request::builder()
        .method("POST")
        .uri("/autogen/api/v1beta/chat/completions")
        .header("Content-Type", "application/json")
        .header("x-openwebui-user-id", malicious_header)
        .body(Body::from(payload.to_string()));

    // Verify that the http crate itself prevents header injection by returning an error
    assert!(res.is_err());
}
pub mod sanitization_test;
