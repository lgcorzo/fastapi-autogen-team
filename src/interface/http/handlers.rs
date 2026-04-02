use axum::{
    extract::State,
    http::{HeaderMap, StatusCode},
    response::{IntoResponse, Response, Sse, sse::Event},
    Json,
};
use futures::StreamExt;
use std::sync::Arc;
use std::convert::Infallible;
use serde_json::json;
use crate::interface::http::routes::AppState;
use crate::application::dtos::Input;

pub async fn docs_redirect() -> impl IntoResponse {
    axum::response::Redirect::temporary("/autogen/api/v1beta/docs")
}

pub async fn get_models() -> impl IntoResponse {
    let model_info = json!({
        "data": {
            "id": "internal-gpt4_v0.1",
            "name": "internal-gpt",
            "description": "This is a state-of-the-art model (Rust version).",
        }
    });
    Json(model_info)
}

pub async fn route_query(
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
