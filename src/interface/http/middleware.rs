use axum::http::{HeaderName, HeaderValue};
use std::env;
use tower_http::cors::{AllowOrigin, CorsLayer};
use tower_http::set_header::SetResponseHeaderLayer;

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
            HeaderValue::from_static(
                "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self';",
            ),
        ),
        SetResponseHeaderLayer::if_not_present(
            HeaderName::from_static("referrer-policy"),
            HeaderValue::from_static("strict-origin-when-cross-origin"),
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
                    .filter_map(|s| {
                        let trimmed = s.trim();
                        if trimmed.is_empty() {
                            None
                        } else {
                            trimmed.parse::<HeaderValue>().ok()
                        }
                    })
                    .collect::<Vec<_>>();

                if origins.is_empty() {
                    return None;
                }

                cors.allow_origin(AllowOrigin::list(origins))
            };
            return Some(cors);
        }
    }
    None
}
