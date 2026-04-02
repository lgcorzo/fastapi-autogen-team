use axum::http::{HeaderName, HeaderValue};
use tower_http::cors::{AllowOrigin, CorsLayer};
use tower_http::set_header::SetResponseHeaderLayer;
use std::env;

pub fn security_headers() -> Vec<SetResponseHeaderLayer<HeaderValue>> {
    vec![
        SetResponseHeaderLayer::if_not_present(
            HeaderName::from_static("x-content-type-options"),
            HeaderValue::from_static("nosniff"),
        ),
        SetResponseHeaderLayer::if_not_present(
            HeaderName::from_static("x-frame-options"),
            HeaderValue::from_static("DENY"),
        ),
        SetResponseHeaderLayer::if_not_present(
            HeaderName::from_static("strict-transport-security"),
            HeaderValue::from_static("max-age=31536000; includeSubDomains"),
        ),
        SetResponseHeaderLayer::if_not_present(
            HeaderName::from_static("content-security-policy"),
            HeaderValue::from_static("default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: https://fastapi.tiangolo.com;"),
        ),
    ]
}

pub fn cors_layer() -> Option<CorsLayer> {
    if let Ok(origins_str) = env::var("ALLOWED_ORIGINS") {
        if !origins_str.trim().is_empty() {
            let cors = CorsLayer::new()
                .allow_methods(tower_http::cors::Any)
                .allow_headers(tower_http::cors::Any);

            let cors = if origins_str == "*" {
                cors.allow_origin(tower_http::cors::Any)
            } else {
                let origins = origins_str
                    .split(',')
                    .map(|s| s.trim().parse::<HeaderValue>().unwrap())
                    .collect::<Vec<_>>();
                cors.allow_origin(AllowOrigin::list(origins))
            };
            return Some(cors);
        }
    }
    None
}
