use fastapi_autogen_team::application::dtos::{ContentType, Input, Message};
use fastapi_autogen_team::domain::agent::team::AgentTeam;
use mockito::Server;

fn make_input(text: &str) -> Input {
    Input {
        model: "test".to_string(),
        messages: vec![Message {
            role: "user".to_string(),
            content: ContentType::String(text.to_string()),
            name: None,
        }],
        stream: Some(false),
        temperature: None,
        user: None,
        top_p: None,
        presence_penalty: None,
        frequency_penalty: None,
    }
}

#[tokio::test]
async fn test_agent_team_run_error() {
    let mut server = Server::new_async().await;
    let url = server.url();
    let team = AgentTeam::new_test(&url);

    let _m = server
        .mock("POST", "/chat/completions")
        .with_status(500)
        .create_async()
        .await;

    let res = team.run(make_input("test")).await;
    assert!(res.is_err());
}

#[tokio::test]
async fn test_agent_team_run_stream_error_on_planner_failure() {
    let mut server = Server::new_async().await;
    let url = server.url();
    let team = AgentTeam::new_test(&url);

    // Planner call fails → run_stream should return Err (before any events)
    let _m = server
        .mock("POST", "/chat/completions")
        .with_status(500)
        .create_async()
        .await;

    let res = team.run_stream(make_input("test")).await;
    assert!(
        res.is_err(),
        "run_stream should propagate planner failure as Err"
    );
}
