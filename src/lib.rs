pub mod data_model;
pub mod telemetry;
pub mod tools;
pub mod agents;

use axum::{
    routing::{get, post},
    Router, Json,
    extract::State,
    http::StatusCode,
    response::{IntoResponse, Response},
};
use std::sync::Arc;
use tower_http::cors::{CorsLayer, Any};
use crate::data_model::Input;
use crate::agents::AgentTeam;
use serde_json::json;

pub struct AppState {
    pub team: AgentTeam,
}

pub fn create_app(state: Arc<AppState>) -> Router {
    Router::new()
        .route("/autogen", get(docs_redirect))
        .route("/autogen/api/v1beta/models", get(get_models))
        .route("/autogen/api/v1beta/chat/completions", post(route_query))
        .layer(CorsLayer::new().allow_origin(Any).allow_methods(Any).allow_headers(Any))
        .with_state(state)
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
    Json(payload): Json<Input>,
) -> Response {
    tracing::info!("Chat completion request for model: {}", payload.model);
    
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
