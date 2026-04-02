use rig::providers::openai;
use rig::completion::Prompt;
use rig::client::CompletionClient;
use crate::tools::SearchTool;
use crate::data_model::Input;
use std::env;

pub struct AgentTeam {
    client: openai::Client,
}

impl AgentTeam {
    pub async fn new() -> anyhow::Result<Self> {
        let api_key = env::var("LITELLM_API_KEY").expect("LITELLM_API_KEY must be set");
        let base_url = env::var("LITELLM_BASE_URL").unwrap_or_else(|_| "http://litellm:4000/v1".to_string());
        
        // Rig 0.34.0 OpenAI client builder
        let client = openai::Client::builder()
            .api_key(&api_key)
            .base_url(&base_url)
            .build()?;

        Ok(Self { client })
    }

    pub async fn run(&self, input: Input) -> anyhow::Result<String> {
        // 1. Planner Agent: Decompose query
        let planner = self.client.agent("gpt-4o")
            .preamble("You are the Planner. Analyze the user message and break it down into focused search queries in English. Return only the queries, one per line.")
            .build();

        let last_message = input.messages.last()
            .and_then(|m| match &m.content {
                crate::data_model::ContentType::String(s) => Some(s.clone()),
                _ => None,
            })
            .unwrap_or_default();

        let queries = planner.prompt(&last_message).await?;
        tracing::info!("Planner queries: {}", queries);

        // 2. RAG Searcher: Execute tools
        let rag_searcher = self.client.agent("gpt-4o")
            .preamble("You are the RAG_searcher. Use the search tool to find information.")
            .tool(SearchTool)
            .build();

        let mut all_results = String::new();
        for query in queries.lines() {
            if query.trim().is_empty() { continue; }
            let res = rag_searcher.prompt(query).await?;
            all_results.push_str(&res);
            all_results.push_str("\n---\n");
        }

        // 3. QA Agent: Final Synthesis
        let qa = self.client.agent("gpt-4o")
            .preamble("You are the Quality Assurance agent. Synthesize the results into a final response in the user's original language. End with TERMINATE.")
            .build();

        let final_response = qa.prompt(format!("User query: {}\n\nResults found:\n{}", last_message, all_results)).await?;

        Ok(final_response)
    }
    pub fn new_mock() -> Self {
        let client = openai::Client::builder()
            .api_key("none")
            .build()
            .unwrap();
        Self { client }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::data_model::{Message, ContentType};
    use mockito::Server;
    use serde_json::json;

    #[tokio::test]
    async fn test_agent_team_orchestration() {
        let mut server = Server::new_async().await;
        let url = server.url();

        // 1. Setup Env for mock client
        env::set_var("LITELLM_API_KEY", "test_key");
        env::set_var("LITELLM_BASE_URL", &url);

        // 2. Mock Planner Response
        let _m_planner = server.mock("POST", mockito::Matcher::Any)
            .match_body(mockito::Matcher::Any)
            .with_status(200)
            .with_header("content-type", "application/json")
            .with_body(json!({
                "id": "planner-1",
                "object": "response",
                "created_at": 12345,
                "status": "completed",
                "model": "gpt-4o",
                "output": [{
                    "type": "message",
                    "id": "msg-p1",
                    "role": "assistant",
                    "status": "completed",
                    "content": [{"type": "output_text", "text": "test search query 1"}]
                }]
            }).to_string())
            .create_async().await;

        // 3. Mock RAG Searcher (Tool use)
        // Rig will first request the tool call
        let _m_searcher_tool = server.mock("POST", mockito::Matcher::Any)
            .match_body(mockito::Matcher::Any)
            .with_status(200)
            .with_header("content-type", "application/json")
            .with_body(json!({
                "id": "searcher-1",
                "object": "response",
                "created_at": 12346,
                "status": "completed",
                "model": "gpt-4o",
                "output": [{
                    "type": "message",
                    "id": "msg-s1",
                    "role": "assistant",
                    "status": "completed",
                    "content": [{"type": "output_text", "text": "I found these results: ..."}]
                }]
            }).to_string())
            .create_async().await;

        // 4. Mock QA Synthesis
        let _m_qa = server.mock("POST", mockito::Matcher::Any)
            .match_body(mockito::Matcher::Any)
            .with_status(200)
            .with_header("content-type", "application/json")
            .with_body(json!({
                "id": "qa-1",
                "object": "response",
                "created_at": 12347,
                "status": "completed",
                "model": "gpt-4o",
                "output": [{
                    "type": "message",
                    "id": "msg-q1",
                    "role": "assistant",
                    "status": "completed",
                    "content": [{"type": "output_text", "text": "FINAL ANSWER: TERMINATE"}]
                }]
            }).to_string())
            .create_async().await;


        // Execute test
        let team = AgentTeam::new().await.unwrap();
        let input = Input {
            model: "test".to_string(),
            user: None,
            messages: vec![Message { role: "user".to_string(), content: ContentType::String("Please help me find...".to_string()), name: None }],
            temperature: None,
            top_p: None,
            presence_penalty: None,
            frequency_penalty: None,
            stream: None,
        };

        let result = team.run(input).await.unwrap();
        assert!(result.contains("TERMINATE"));
    }
}

