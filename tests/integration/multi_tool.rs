use mockito::Server;
use rust_agent_team::application::dtos::{ContentType, Input, Message};
use rust_agent_team::domain::agent::team::{AgentEvent, AgentTeam};
use std::env;

#[tokio::test]
async fn test_multi_tool_call() {
    let _ = tracing_subscriber::fmt::try_init();
    let mut server = Server::new_async().await;
    let url = server.url();

    // 0. Translator mock
    let _m_translator = server
        .mock("POST", "/chat/completions")
        .with_status(200)
        .with_header("content-type", "application/json")
        .with_body(
            r#"{
            "id": "chatcmpl-0",
            "object": "chat.completion",
            "created": 1677652288,
            "model": "test",
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "Check all three systems"
                },
                "finish_reason": "stop",
                "index": 0
            }],
            "usage": { "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0 }
        }"#,
        )
        .expect(2)
        .create_async()
        .await;

    // 1. Planner mock (First call)
    let _m_planner = server
        .mock("POST", "/chat/completions")
        .with_status(200)
        .with_header("content-type", "application/json")
        .with_body(
            r#"{
            "id": "chatcmpl-1",
            "object": "chat.completion",
            "created": 1677652288,
            "model": "test",
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "[JIRA] status PROJ-123\n[CONFLUENCE] arch doc\n[R2R] fastapi tips"
                },
                "finish_reason": "stop",
                "index": 0
            }],
            "usage": { "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0 }
        }"#,
        )
        .expect(1)
        .create_async()
        .await;

    // 2. Searcher mocks (Next 3 calls)
    // We can use a single mock with expect(3) if they all return the same thing
    let _m_searchers = server
        .mock("POST", "/chat/completions")
        .with_status(200)
        .with_header("content-type", "application/json")
        .with_body(
            r#"{
            "id": "chatcmpl-2",
            "object": "chat.completion",
            "created": 1677652288,
            "model": "test",
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "Search result: found something"
                },
                "finish_reason": "stop",
                "index": 0
            }],
            "usage": { "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0 }
        }"#,
        )
        .expect(3)
        .create_async()
        .await;

    // 3. QA mock (Final call, Streaming)
    let _m_qa = server
        .mock("POST", "/chat/completions")
        .with_status(200)
        .with_header("content-type", "text/event-stream")
        .with_body("data: {\"choices\": [{\"delta\": {\"content\": \"Final synthesis: \"}}]}\n\ndata: {\"choices\": [{\"delta\": {\"content\": \"Everything is okay. TERMINATE\"}}]}\n\ndata: [DONE]\n\n")
        .expect(1)
        .create_async()
        .await;

    env::set_var("LITELLM_API_KEY", "test");
    let team = AgentTeam::new_test(&url);

    let input = Input {
        model: "test-model".to_string(),
        user: None,
        messages: vec![Message {
            role: "user".to_string(),
            content: ContentType::String("Check all three systems".to_string()),
            name: None,
        }],
        temperature: None,
        top_p: None,
        presence_penalty: None,
        frequency_penalty: None,
        stream: Some(true),
    };

    use futures::StreamExt;
    let mut stream = team
        .run_stream(input)
        .await
        .expect("Failed to start stream");

    let mut found_jira = false;
    let mut found_confluence = false;
    let mut found_r2r = false;
    let mut final_content = String::new();

    while let Some(res) = stream.next().await {
        match res {
            Ok(event) => {
                println!("Event: {:?}", event);
                match event {
                    AgentEvent::Progress { message, .. } => {
                        if message.contains("JIRA") {
                            found_jira = true;
                        }
                        if message.contains("CONFLUENCE") {
                            found_confluence = true;
                        }
                        if message.contains("R2R") {
                            found_r2r = true;
                        }
                    }
                    AgentEvent::Delta(delta) => {
                        final_content.push_str(&delta);
                    }
                    AgentEvent::Done => {}
                }
            }
            Err(e) => {
                eprintln!("STREAM ERROR: {:?}", e);
            }
        }
    }

    assert!(found_jira, "Should have called Jira searcher");
    assert!(found_confluence, "Should have called Confluence searcher");
    assert!(found_r2r, "Should have called R2R searcher");
    assert!(
        final_content.contains("Final synthesis"),
        "Should have finished with final synthesis. Content: {}",
        final_content
    );

    println!("SUCCESS: Test reached end successfully!");
    tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
}
