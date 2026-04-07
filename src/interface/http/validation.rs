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

                let details = if status == StatusCode::PAYLOAD_TOO_LARGE {
                    "Payload too large. Please send a smaller request.".to_string()
                } else {
                    "Invalid JSON payload. Please check your request format.".to_string()
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
