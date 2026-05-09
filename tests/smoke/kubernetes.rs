use dotenvy::dotenv;
use futures::StreamExt;
use rust_agent_team::application::dtos::{ContentType, Input, Message};
use rust_agent_team::domain::agent::team::{AgentEvent, AgentTeam};
use std::env;

/// Helper function to determine if the test is running inside a Kubernetes cluster.
fn is_in_kubernetes() -> bool {
    env::var("KUBERNETES_SERVICE_HOST").is_ok()
}

/// Helper function to run the agent team with a specific prompt and check if a specific tool was triggered.
async fn run_kubernetes_agent_test(prompt: &str, expected_tool_indicator: &str) {
    // 1. Skip if not running in a Kubernetes environment
    if !is_in_kubernetes() {
        println!(
            "SKIPPED: '{}' test is only executed inside Kubernetes. (KUBERNETES_SERVICE_HOST not set).",
            expected_tool_indicator
        );
        return;
    }

    // Load environment variables (e.g. from .env if present inside K8s pod)
    dotenv().ok();

    println!("Initializing real AgentTeam for production test inside Kubernetes...");
    let team_res = AgentTeam::new().await;
    let team = match team_res {
        Ok(t) => t,
        Err(e) => {
            panic!("Failed to initialize real AgentTeam in Kubernetes environment: {}", e);
        }
    };

    let input = Input {
        model: "ollama/qwen2.5:7b".to_string(),
        user: Some("k8s-production-test-user".to_string()),
        messages: vec![Message {
            role: "user".to_string(),
            content: ContentType::String(prompt.to_string()),
            name: None,
        }],
        temperature: Some(0.1),
        top_p: None,
        presence_penalty: None,
        frequency_penalty: None,
        stream: Some(true),
    };

    println!("Sending prompt to Agent Team: '{}'", prompt);
    let mut stream = team
        .run_stream(input)
        .await
        .expect("Failed to start Agent Team stream");

    let mut tool_triggered = false;
    let mut final_response = String::new();

    while let Some(res) = stream.next().await {
        match res {
            Ok(event) => {
                println!("[K8S TEST EVENT] {:?}", event);
                match event {
                    AgentEvent::Progress { stage, message } => {
                        println!("Progress ({}): {}", stage, message);
                        if message.to_uppercase().contains(&expected_tool_indicator.to_uppercase()) {
                            tool_triggered = true;
                        }
                    }
                    AgentEvent::Delta(delta) => {
                        final_response.push_str(&delta);
                    }
                    AgentEvent::Done => {
                        println!("Stream completed successfully.");
                    }
                }
            }
            Err(e) => {
                panic!("Stream encountered an error: {:?}", e);
            }
        }
    }

    println!("\n--- Final Synthesized Response ---\n{}", final_response);

    assert!(
        tool_triggered,
        "The agent team did not trigger the expected tool: {}",
        expected_tool_indicator
    );
    assert!(
        !final_response.is_empty(),
        "Agent team returned an empty response"
    );
}

/// PRODUCTION TEST: Verify that the agent successfully accesses R2R (RAG) information inside Kubernetes.
#[tokio::test]
#[ignore]
async fn test_r2r_access_in_kubernetes() {
    run_kubernetes_agent_test(
        "Search our internal R2R knowledge base for any MLOps guidelines or documents.",
        "R2R",
    )
    .await;
}

/// PRODUCTION TEST: Verify that the agent successfully accesses JIRA information inside Kubernetes.
#[tokio::test]
#[ignore]
async fn test_jira_access_in_kubernetes() {
    run_kubernetes_agent_test(
        "Get the status or summary of different JIRA tickets like GITOPS-1 or JIRA-123.",
        "JIRA",
    )
    .await;
}

/// PRODUCTION TEST: Verify that the agent successfully accesses Confluence information inside Kubernetes.
#[tokio::test]
#[ignore]
async fn test_confluence_access_in_kubernetes() {
    run_kubernetes_agent_test(
        "Search Confluence for any documentation or wiki pages about project architecture.",
        "CONFLUENCE",
    )
    .await;
}

/// PRODUCTION TEST: Verify that the agent successfully accesses ALL three systems in a single prompt.
#[tokio::test]
#[ignore]
async fn test_all_tools_access_in_kubernetes() {
    if !is_in_kubernetes() {
        println!("SKIPPED: 'ALL_TOOLS' test is only executed inside Kubernetes.");
        return;
    }

    dotenv().ok();

    let team = AgentTeam::new()
        .await
        .expect("Failed to initialize AgentTeam");

    let input = Input {
        model: "ollama/qwen2.5:7b".to_string(),
        user: Some("k8s-production-test-user".to_string()),
        messages: vec![Message {
            role: "user".to_string(),
            content: ContentType::String(
                "Please search our internal systems: find JIRA tickets about GitOps, check Confluence for architecture, and retrieve R2R general MLOps info.".to_string()
            ),
            name: None,
        }],
        temperature: Some(0.1),
        top_p: None,
        presence_penalty: None,
        frequency_penalty: None,
        stream: Some(true),
    };

    let mut stream = team
        .run_stream(input)
        .await
        .expect("Failed to start Agent Team stream");

    let mut found_jira = false;
    let mut found_confluence = false;
    let mut found_r2r = false;
    let mut final_response = String::new();

    while let Some(res) = stream.next().await {
        match res {
            Ok(event) => {
                match event {
                    AgentEvent::Progress { message, .. } => {
                        println!("Progress: {}", message);
                        let upper = message.to_uppercase();
                        if upper.contains("JIRA") {
                            found_jira = true;
                        }
                        if upper.contains("CONFLUENCE") {
                            found_confluence = true;
                        }
                        if upper.contains("R2R") {
                            found_r2r = true;
                        }
                    }
                    AgentEvent::Delta(delta) => {
                        final_response.push_str(&delta);
                    }
                    AgentEvent::Done => {}
                }
            }
            Err(e) => {
                panic!("Stream encountered an error: {:?}", e);
            }
        }
    }

    assert!(found_jira, "Agent team should have accessed Jira");
    assert!(found_confluence, "Agent team should have accessed Confluence");
    assert!(found_r2r, "Agent team should have accessed R2R");
    assert!(!final_response.is_empty(), "Synthesis response should not be empty");
}
