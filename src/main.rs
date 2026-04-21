use dotenvy::dotenv;
use rust_agent_team::domain::agent::team::AgentTeam;
use rust_agent_team::infrastructure::telemetry;
use rust_agent_team::{create_app, AppState};
use std::env;
use std::sync::Arc;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    dotenv().ok();

    let app_name = env::var("APP_NAME").unwrap_or_else(|_| "Rust-Agent-Service".to_string());
    let otel_endpoint = env::var("DEFAULT_OTEL_ENDPOINT")
        .unwrap_or_else(|_| "http://otel-collector:4318/v1".to_string());
    let host = env::var("DEFAULT_HOST").unwrap_or_else(|_| "127.0.0.1".to_string());
    let port = env::var("DEFAULT_PORT").unwrap_or_else(|_| "4100".to_string());

    // Initialize Telemetry
    telemetry::init_telemetry(&app_name, &otel_endpoint)?;

    // Initialize State
    let team = AgentTeam::new().await?;
    let state = Arc::new(AppState { team });

    // Routing
    let app = create_app(state);

    let addr = format!("{}:{}", host, port);
    tracing::info!("Listening on {}", addr);

    let listener = tokio::net::TcpListener::bind(&addr).await?;
    axum::serve(listener, app).await?;

    Ok(())
}
