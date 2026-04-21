use crate::domain::agent::team::AgentTeam;
use crate::interface::http::handlers::{docs_redirect, get_models, route_query};
use crate::interface::http::middleware::{cors_layer, security_headers};
use axum::{
    routing::{get, post},
    Router,
};
use std::sync::Arc;
use tower_http::trace::TraceLayer;

pub struct AppState {
    pub team: AgentTeam,
}

pub fn create_app(state: Arc<AppState>) -> Router {
    let mut router = Router::new()
        .route("/agent", get(docs_redirect))
        .nest(
            "/agent/api/v1beta",
            Router::new()
                .route("/models", get(get_models))
                .route("/chat/completions", post(route_query)),
        )
        .with_state(state);

    // Apply security headers
    for layer in security_headers() {
        router = router.layer(layer);
    }

    // Apply CORS
    if let Some(cors) = cors_layer() {
        router = router.layer(cors);
    }
    router.layer(TraceLayer::new_for_http())
}
