use axum::{
    body::Body,
    http::{self, Request, StatusCode},
};
use dotenvy::dotenv;
use http_body_util::BodyExt;
use rust_agent_team::application::dtos::{ContentType, Input, Message};
use rust_agent_team::domain::agent::team::AgentTeam;
use rust_agent_team::{create_app, AppState};
use std::sync::Arc;
use tower::ServiceExt;

/// PRODUCTION SMOKE TEST
/// This test verifies that the system can connect to:
/// 1. LiteLLM (OpenAI Compatible)
/// 2. Jira
/// 3. R2R (RAG)
///
/// CAUTION: This test consumes real LLM tokens and makes live requests.
/// It is ignored by default. Run with `cargo test --test smoke_tests -- --ignored`.
#[tokio::test]
#[ignore]
async fn test_production_pipeline_smoke() {
    // 1. Load environment variables
    dotenv().ok();

    // 2. Initialize real infrastructure
    // These require real secrets in your .env or environment
    let team_res = AgentTeam::new().await;

    match team_res {
        Ok(team) => {
            let state = Arc::new(AppState { team });
            let app = create_app(state);

            let input = Input {
                model: "minimax-m2.7:cloud".to_string(), // Adjust based on your LiteLLM config
                user: Some("smoke-test-user".to_string()),
                messages: vec![Message {
                    role: "user".to_string(),
                    content: ContentType::String(
                        "que es el mlops y como se define un proyecto por pasos".to_string(),
                    ),
                    name: None,
                }],
                temperature: Some(0.1),
                top_p: None,
                presence_penalty: None,
                frequency_penalty: None,
                stream: Some(false),
            };

            // 3. Send real POST request
            let response = app
                .oneshot(
                    Request::builder()
                        .method(http::Method::POST)
                        .uri("/agent/api/v1beta/chat/completions")
                        .header(http::header::CONTENT_TYPE, "application/json")
                        .body(Body::from(serde_json::to_vec(&input).unwrap()))
                        .unwrap(),
                )
                .await
                .expect("Failed to get response from app");

            // 4. Assert Success
            assert_eq!(
                response.status(),
                StatusCode::OK,
                "Standard Pipeline Failed"
            );

            let body = response
                .into_body()
                .collect()
                .await
                .expect("Failed to read body")
                .to_bytes();
            let body_str = String::from_utf8_lossy(&body);
            tracing::info!("Smoke test response body: {}", body_str);

            assert!(
                body_str.contains("choices"),
                "Response body does not contain choices"
            );
            assert!(
                body_str.contains("TERMINATE") || body_str.len() > 100,
                "Response seems too short or invalid"
            );
        }
        Err(e) => {
            panic!("Failed to initialize real AgentTeam for smoke test. Check your environment variables: {}", e);
        }
    }
}

pub mod kubernetes;

