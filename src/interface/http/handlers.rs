use axum::{
    extract::State,
    http::{HeaderMap, StatusCode},
    response::{sse::Event, IntoResponse, Sse},
    Json,
};
use futures::StreamExt;
use std::sync::Arc;
use std::convert::Infallible;
use serde_json::json;

use crate::interface::http::routes::AppState;
use crate::application::dtos::Input;
use crate::interface::http::validation::ValidatedJson;

pub async fn docs_redirect() -> impl IntoResponse {
    (StatusCode::SEE_OTHER, [("Location", "https://autogen-team.com/docs")])
}

pub async fn get_models() -> impl IntoResponse {
    let model_info = json!({
        "object": "list",
        "data": [
            {
                "id": "minimax-m2.7:cloud",
                "object": "model",
                "created": 1686935002,
                "owned_by": "openai-compatible",
                "permission": [],
                "root": "minimax-m2.7:cloud",
                "parent": null,
            }
        ]
    });
    Json(model_info)
}

pub async fn route_query(
    State(state): State<Arc<AppState>>,
    headers: HeaderMap,
    ValidatedJson(request): ValidatedJson<Input>,
) -> impl IntoResponse {
    // Basic Header Sanitization (example: carry over authorization if needed)
    let _auth = headers.get("authorization");
    
    // Validation: Empty messages
    if request.messages.is_empty() {
        return (StatusCode::UNPROCESSABLE_ENTITY, Json(json!({
            "error": "Unprocessable Entity",
            "details": "messages list cannot be empty"
        }))).into_response();
    }
    
    if request.stream.unwrap_or(false) {
        let stream = state.team.run_stream(request).await.unwrap();
        let sse_stream = stream.map(|res| {
            let content = res.unwrap_or_else(|e| format!("Error: {}", e));
            let chunk = json!({
                "choices": [{
                    "delta": { "content": content },
                    "index": 0,
                    "finish_reason": if content.contains("TERMINATE") { Some("stop") } else { None }
                }]
            });
            Ok::<Event, Infallible>(Event::default().data(chunk.to_string()))
        });
        return Sse::new(sse_stream).keep_alive(axum::response::sse::KeepAlive::default()).into_response();
    }

    let response = state.team.run(request).await.unwrap_or_else(|e| format!("Error: {}", e));
    
    let output = json!({
        "id": "chatcmpl-default",
        "object": "chat.completion",
        "created": chrono::Utc::now().timestamp(),
        "model": "minimax-m2.7:cloud",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": response,
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


