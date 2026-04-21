use mockito::Server;
use rust_agent_team::application::dtos::{ContentType, Input, Message};
use rust_agent_team::domain::agent::team::AgentTeam;

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

    // Planner call fails → run_stream returns Ok(stream), but stream yields Err
    let _m = server
        .mock("POST", "/chat/completions")
        .with_status(500)
        .create_async()
        .await;

    let res = team.run_stream(make_input("test")).await;
    assert!(
        res.is_ok(),
        "run_stream should return Ok(stream) even if planner fails later"
    );

    let mut stream = res.unwrap();
    use futures::StreamExt;
    let first_item = stream.next().await;
    assert!(first_item.is_some());
    assert!(
        first_item.unwrap().is_err(),
        "First stream item should be an error on planner failure"
    );
}
