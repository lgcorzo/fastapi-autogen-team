use axum::{
    extract::Query,
    routing::{get, post},
    Json, Router,
};
use serde::Deserialize;
use serde_json::{json, Value};
use std::net::SocketAddr;
use std::sync::Arc;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

#[derive(Clone)]
struct AppState {}

#[tokio::main]
async fn main() {
    tracing_subscriber::registry()
        .with(tracing_subscriber::fmt::layer())
        .with(tracing_subscriber::EnvFilter::new("info"))
        .init();

    let state = Arc::new(AppState {});

    let app = Router::new()
        .route("/", get(|| async { "Mock Services Running" }))
        // R2R Mocks
        .route("/v3/users/login", post(r2r_login))
        .route("/v3/retrieval/rag", post(r2r_rag))
        .route("/v3/retrieval/search", post(r2r_search))
        // Jira Mocks
        .route("/rest/api/2/search", get(jira_search))
        .with_state(state);

    let addr = SocketAddr::from(([127, 0, 0, 1], 8081));
    tracing::info!("Mock server listening on {}", addr);
    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}

async fn r2r_login() -> Json<Value> {
    tracing::info!("R2R Login called");
    Json(json!({
        "results": {
            "access_token": {
                "token": "mock_access_token_v3"
            }
        }
    }))
}

async fn r2r_rag(Json(payload): Json<Value>) -> Json<Value> {
    tracing::info!("R2R RAG called with: {}", payload);
    Json(json!({
        "results": {
            "generated_answer": "This is a mocked R2R RAG response for internal documentation search."
        }
    }))
}

async fn r2r_search(Json(payload): Json<Value>) -> Json<Value> {
    tracing::info!("R2R search called with: {}", payload);
    Json(json!({
        "results": {
            "chunk_search_results": [
                {
                    "text": "This is the first piece of mocked search result content from R2R."
                },
                {
                    "text": "This is the second piece of mocked search result content from R2R, providing more context."
                }
            ]
        }
    }))
}

#[derive(Deserialize)]
struct JiraQueryParams {
    jql: Option<String>,
}

async fn jira_search(Query(params): Query<JiraQueryParams>) -> Json<Value> {
    tracing::info!("Jira search called with JQL: {:?}", params.jql);
    Json(json!({
        "issues": [
            {
                "key": "MOCK-1",
                "fields": {
                    "summary": "Mocked Jira Issue 1"
                }
            },
            {
                "key": "MOCK-2",
                "fields": {
                    "summary": "Mocked Jira Issue 2"
                }
            }
        ]
    }))
}
