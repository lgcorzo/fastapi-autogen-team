use axum::{
    async_trait,
    extract::{FromRequest, Request},
    http::StatusCode,
    response::{IntoResponse, Response},
    Json,
};
use serde::de::DeserializeOwned;

pub struct ValidatedJson<T>(pub T);

#[async_trait]
impl<S, T> FromRequest<S> for ValidatedJson<T>
where
    T: DeserializeOwned,
    S: Send + Sync,
{
    type Rejection = Response;

    async fn from_request(req: Request, state: &S) -> Result<Self, Self::Rejection> {
        match Json::<T>::from_request(req, state).await {
            Ok(Json(value)) => Ok(ValidatedJson(value)),
            Err(rejection) => {
                let status = match rejection.status() {
                    StatusCode::PAYLOAD_TOO_LARGE => StatusCode::PAYLOAD_TOO_LARGE,
                    _ => StatusCode::UNPROCESSABLE_ENTITY,
                };

                // Log the detailed error internally to prevent information leakage
                tracing::error!("JSON validation rejection: {}", rejection);

                let details = match status {
                    StatusCode::PAYLOAD_TOO_LARGE => {
                        "The request payload exceeds the maximum allowed size."
                    }
                    _ => "Failed to parse request body as JSON or invalid payload structure.",
                };

                let body = Json(serde_json::json!({
                    "error": status.canonical_reason().unwrap_or("Error"),
                    "details": details
                }));
                Err((status, body).into_response())
            }
        }
    }
}
