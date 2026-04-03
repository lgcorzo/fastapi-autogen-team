use fastapi_autogen_team::interface::http::handlers::{docs_redirect, get_models, route_query};
use fastapi_autogen_team::interface::http::routes::AppState;
use fastapi_autogen_team::application::dtos::{Input, Message, ContentType};
use fastapi_autogen_team::domain::agent::team::AgentTeam;
use axum::{
    extract::State,
    Json,
    http::{StatusCode, HeaderMap},
    response::IntoResponse,
};
use std::sync::Arc;

#[tokio::test]
async fn test_docs_redirect() {
    let res = docs_redirect().await;
    let response = res.into_response();
    assert_eq!(response.status(), StatusCode::SEE_OTHER);
    assert_eq!(response.headers().get("Location").unwrap(), "https://autogen-team.com/docs");
}

#[tokio::test]
async fn test_get_models() {
    let res = get_models().await;
    let response = res.into_response();
    assert_eq!(response.status(), StatusCode::OK);
}

#[tokio::test]
async fn test_route_query_no_stream() {
    let state = Arc::new(AppState { team: AgentTeam::new_mock() });
    let request = Input {
        model: "test".to_string(),
        messages: vec![Message {
            role: "user".to_string(),
            content: ContentType::String("hello".to_string()),
            name: None,
        }],
        stream: Some(false),
        temperature: None,
        user: None,
        top_p: None,
        presence_penalty: None,
        frequency_penalty: None,
    };
    
    let mut headers = HeaderMap::new();
    headers.insert("authorization", "Bearer test".parse().unwrap());

    let res = route_query(State(state), headers, Json(request)).await;
    let response = res.into_response();
    assert_eq!(response.status(), StatusCode::OK);
}
