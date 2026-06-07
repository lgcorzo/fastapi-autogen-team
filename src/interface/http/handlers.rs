use axum::{
    extract::State,
    http::{HeaderMap, StatusCode},
    response::{sse::Event, IntoResponse, Sse},
    Json,
};
use futures::StreamExt;
use serde_json::json;
use std::convert::Infallible;
use std::sync::Arc;

use crate::application::dtos::Input;
use crate::domain::agent::team::AgentEvent;
use crate::interface::http::routes::AppState;
use crate::interface::http::validation::ValidatedJson;

pub async fn docs_redirect() -> impl IntoResponse {
    (
        StatusCode::SEE_OTHER,
        [("Location", "https://agent-team.com/docs")],
    )
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
    // Basic Header Sanitization
    let _auth = headers.get("authorization");

    // Validation: Empty messages
    if request.messages.is_empty() {
        return (
            StatusCode::UNPROCESSABLE_ENTITY,
            Json(json!({
                "error": "Unprocessable Entity",
                "details": "messages list cannot be empty"
            })),
        )
            .into_response();
    }

    if request.stream.unwrap_or(false) {
        let model = request.model.clone();
        match state.team.run_stream(request).await {
            Ok(stream) => {
                let id = format!("chatcmpl-{}", chrono::Utc::now().timestamp_millis());
                let created = chrono::Utc::now().timestamp() as u64;

                let id_role = id.clone();
                let model_role = model.clone();
                let role_chunk = json!({
                    "id": id_role,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": model_role,
                    "choices": [{
                        "delta": { "role": "assistant" },
                        "index": 0,
                        "finish_reason": null
                    }]
                });

                let role_stream = futures::stream::once(async move {
                    Ok::<Event, Infallible>(Event::default().data(role_chunk.to_string()))
                });

                let content_stream = stream.map(move |res| -> Result<Event, Infallible> {
                    match res {
                        // --- Progress event: planner / searcher stage update ---
                        Ok(AgentEvent::Progress { stage, message }) => {
                            let chunk = json!({
                                "id": id,
                                "object": "chat.completion.chunk",
                                "created": created,
                                "model": model,
                                "choices": [{
                                    "delta": {
                                        "content": format!("<think>[{}] {}</think>\n", stage, message),
                                        "reasoning_content": format!("[{}] {}\n", stage, message)
                                    },
                                    "index": 0,
                                    "finish_reason": null
                                }]
                            });
                            Ok(Event::default().data(chunk.to_string()))
                        }

                        // --- Delta event: a single QA streaming token ---
                        Ok(AgentEvent::Delta(content)) => {
                            let finish_reason = if content.contains("TERMINATE") {
                                Some("stop")
                            } else {
                                None
                            };
                            let chunk = json!({
                                "id": id,
                                "object": "chat.completion.chunk",
                                "created": created,
                                "model": model,
                                "choices": [{
                                    "delta": { "content": content },
                                    "index": 0,
                                    "finish_reason": finish_reason
                                }]
                            });
                            Ok(Event::default().data(chunk.to_string()))
                        }

                        // --- Done event: pipeline fully completed ---
                        Ok(AgentEvent::Done) => Ok(Event::default().data("[DONE]")),

                        // --- Error: surface as a delta with error content ---
                        Err(e) => {
                            tracing::error!("Stream error: {}", e);
                            let chunk = json!({
                                "id": id,
                                "object": "chat.completion.chunk",
                                "created": created,
                                "model": model,
                                "choices": [{
                                    "delta": {
                                        "content": "\nError: An error occurred while processing the request."
                                    },
                                    "index": 0,
                                    "finish_reason": "stop"
                                }]
                            });
                            Ok(Event::default().data(chunk.to_string()))
                        }
                    }
                });

                let sse_stream = role_stream.chain(content_stream);
                return Sse::new(sse_stream)
                    .keep_alive(axum::response::sse::KeepAlive::default())
                    .into_response();
            }
            Err(e) => {
                tracing::error!("Error initializing stream: {}", e);
                let once_stream = futures::stream::once(async move {
                    Ok::<Event, Infallible>(Event::default().data("[DONE]"))
                });
                return Sse::new(once_stream)
                    .keep_alive(axum::response::sse::KeepAlive::default())
                    .into_response();
            }
        }
    }

    // Non-streaming path — unchanged
    let response = match state.team.run(request).await {
        Ok(res) => res,
        Err(e) => {
            tracing::error!("Error running team: {}", e);
            return (
                StatusCode::INTERNAL_SERVER_ERROR,
                Json(json!({
                    "error": "Internal Server Error",
                    "details": "An error occurred while processing the request."
                })),
            )
                .into_response();
        }
    };

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
