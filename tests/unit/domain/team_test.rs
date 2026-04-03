use fastapi_autogen_team::application::dtos::{ContentType, Input, Message};
use fastapi_autogen_team::domain::agent::team::AgentTeam;
use mockito::Server;

#[tokio::test]
async fn test_agent_team_run_error() {
    let mut server = Server::new_async().await;
    let url = server.url();
    let team = AgentTeam::new_test(&url);

    let input = Input {
        model: "test".to_string(),
        messages: vec![Message {
            role: "user".to_string(),
            content: ContentType::String("test".to_string()),
            name: None,
        }],
        stream: Some(false),
        temperature: None,
        user: None,
        top_p: None,
        presence_penalty: None,
        frequency_penalty: None,
    };

    // Mock error for OpenAI call
    // Note: Rig might use /chat/completions or /completions depending on configuration.
    // In the execution code, it uses .completions_api() which usually maps to /chat/completions for OpenAI.
    let _m = server
        .mock("POST", "/chat/completions")
        .with_status(500)
        .create_async()
        .await;

    let res = team.run(input).await;
    assert!(res.is_err());
}
