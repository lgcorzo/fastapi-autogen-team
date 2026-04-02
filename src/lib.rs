pub mod data_model;
pub mod telemetry;
pub mod tools;
pub mod agents;

use axum::{
    routing::{get, post},
    Router, Json,
    extract::State,
    http::{StatusCode, HeaderMap, HeaderName, HeaderValue},
    response::{IntoResponse, Response, Sse, sse::Event},
};
use futures::StreamExt;
use std::sync::Arc;
use std::convert::Infallible;
use tower_http::cors::{CorsLayer, AllowOrigin};
use tower_http::set_header::SetResponseHeaderLayer;
use crate::data_model::Input;
use crate::agents::AgentTeam;
use serde_json::json;

pub struct AppState {
    pub team: AgentTeam,
}

pub fn create_app(state: Arc<AppState>) -> Router {
    let mut router = Router::new()
        .route("/autogen", get(docs_redirect))
        .route("/autogen/api/v1beta/models", get(get_models))
        .route("/autogen/api/v1beta/chat/completions", post(route_query))
        .with_state(state);

    // Security Headers
    router = router
        .layer(SetResponseHeaderLayer::if_not_present(
            HeaderName::from_static("x-content-type-options"),
            HeaderValue::from_static("nosniff"),
        ))
        .layer(SetResponseHeaderLayer::if_not_present(
            HeaderName::from_static("x-frame-options"),
            HeaderValue::from_static("DENY"),
        ))
        .layer(SetResponseHeaderLayer::if_not_present(
            HeaderName::from_static("strict-transport-security"),
            HeaderValue::from_static("max-age=31536000; includeSubDomains"),
        ))
        .layer(SetResponseHeaderLayer::if_not_present(
            HeaderName::from_static("content-security-policy"),
            HeaderValue::from_static("default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: https://fastapi.tiangolo.com;"),
        ));

    // CORS
    if let Ok(origins_str) = std::env::var("ALLOWED_ORIGINS") {
        if !origins_str.trim().is_empty() {
            let origins = origins_str
                .split(',')
                .map(|s| s.trim().parse::<HeaderValue>().unwrap())
                .collect::<Vec<_>>();
            router = router.layer(
                CorsLayer::new()
                    .allow_origin(AllowOrigin::list(origins))
                    .allow_methods(tower_http::cors::Any)
                    .allow_headers(tower_http::cors::Any),
            );
        }
    }

    router
}

async fn docs_redirect() -> impl IntoResponse {
    axum::response::Redirect::temporary("/autogen/api/v1beta/docs")
}

async fn get_models() -> impl IntoResponse {
    let model_info = json!({
        "data": {
            "id": "internal-gpt4_v0.1",
            "name": "internal-gpt",
            "description": "This is a state-of-the-art model (Rust version).",
        }
    });
    Json(model_info)
}

async fn route_query(
    State(state): State<Arc<AppState>>,
    headers: HeaderMap,
    Json(mut payload): Json<Input>,
) -> Response {
    // Sanitization: Escape CRLF in x-openwebui-user-id to prevent injection
    if let Some(user_id) = headers.get("x-openwebui-user-id") {
        if let Ok(user_str) = user_id.to_str() {
            let sanitized = user_str.replace('\r', "\\r").replace('\n', "\\n");
            payload.user = Some(sanitized);
        }
    }

    if payload.stream == Some(true) {
        match state.team.run_stream(payload).await {
            Ok(stream) => {
                let sse_stream = stream.map(|res: anyhow::Result<String>| {
                    match res {
                        Ok(content) => {
                            let chunk = json!({
                                "id": "rust-stream-123",
                                "object": "chat.completion.chunk",
                                "created": chrono::Utc::now().timestamp(),
                                "model": "internal-gpt",
                                "choices": [{
                                    "delta": {
                                        "content": content
                                    },
                                    "index": 0,
                                    "finish_reason": null
                                }]
                            });
                            Ok::<Event, Infallible>(Event::default().data(chunk.to_string()))
                        }
                        Err(e) => {
                            tracing::error!("Stream error: {}", e);
                            Ok::<Event, Infallible>(Event::default().data("Stream error occurred"))
                        }
                    }
                });
                return Sse::new(sse_stream).into_response();
            }
            Err(e) => {
                tracing::error!("Error starting stream: {}", e);
                return (StatusCode::INTERNAL_SERVER_ERROR, "An internal error occurred").into_response();
            }
        }
    }

    match state.team.run(payload).await {
        Ok(response) => {
            let output = json!({
                "id": "rust-run-123",
                "object": "chat.completion",
                "created": chrono::Utc::now().timestamp(),
                "model": "internal-gpt",
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": response
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            });
            Json(output).into_response()
        }
        Err(e) => {
            tracing::error!("Error in agent team: {}", e);
            (StatusCode::INTERNAL_SERVER_ERROR, "An internal error occurred").into_response()
        }
    }
}
