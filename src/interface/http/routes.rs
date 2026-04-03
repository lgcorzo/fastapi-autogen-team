use crate::domain::agent::team::AgentTeam;
use crate::interface::http::handlers::{docs_redirect, get_models, route_query};
use crate::interface::http::middleware::{cors_layer, security_headers};
use axum::{
    routing::{get, post},
    Router,
};
use std::sync::Arc;

pub struct AppState {
    pub team: AgentTeam,
}

pub fn create_app(state: Arc<AppState>) -> Router {
    let mut router = Router::new()
        .route("/autogen", get(docs_redirect))
        .route("/autogen/api/v1beta/models", get(get_models))
        .route("/autogen/api/v1beta/chat/completions", post(route_query))
        .with_state(state);

    // Apply security headers
    for layer in security_headers() {
        router = router.layer(layer);
    }

    // Apply CORS
    if let Some(cors) = cors_layer() {
        router = router.layer(cors);
    }

    router
}
