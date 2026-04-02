use rig::providers::openai;
use rig::completion::{Prompt};
use rig::streaming::StreamingPrompt;
use rig::client::CompletionClient;
use crate::infrastructure::tools::search::SearchTool;
use crate::application::dtos::Input;
use std::env;
use futures::StreamExt;

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
        let planner = self.client.agent("minimax-m2.7:cloud")
            .preamble("You are the Planner. Analyze the user message and break it down into focused search queries in English. Return only the queries, one per line.")
            .build();

        let last_message = input.messages.last()
            .and_then(|m| match &m.content {
                crate::application::dtos::ContentType::String(s) => Some(s.clone()),
                _ => None,
            })
            .unwrap_or_default();

        let queries = planner.prompt(&last_message).await?;
        tracing::info!("Planner queries: {}", queries);

        // 2. RAG Searcher: Execute tools
        let rag_searcher = self.client.agent("minimax-m2.7:cloud")
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
        let qa = self.client.agent("minimax-m2.7:cloud")
            .preamble("You are the Quality Assurance agent. Synthesize the results into a final response in the user's original language. End with TERMINATE.")
            .build();

        let final_response = qa.prompt(format!("User query: {}\n\nResults found:\n{}", last_message, all_results)).await?;

        Ok(final_response)
    }

    pub async fn run_stream(&self, input: Input) -> anyhow::Result<impl futures::Stream<Item = anyhow::Result<String>>> {
        // 1. Planner Agent: Decompose query
        let planner = self.client.agent("minimax-m2.7:cloud")
            .preamble("You are the Planner. Analyze the user message and break it down into focused search queries in English. Return only the queries, one per line.")
            .build();

        let last_message = input.messages.last()
            .and_then(|m| match &m.content {
                crate::application::dtos::ContentType::String(s) => Some(s.clone()),
                _ => None,
            })
            .unwrap_or_default();

        let queries = planner.prompt(&last_message).await?;

        // 2. RAG Searcher: Execute tools
        let rag_searcher = self.client.agent("minimax-m2.7:cloud")
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

        // 3. QA Agent: Final Synthesis (Streaming)
        let qa = self.client.agent("minimax-m2.7:cloud")
            .preamble("You are the Quality Assurance agent. Synthesize the results into a final response in the user's original language. End with TERMINATE.")
            .build();

        let stream = qa.stream_prompt(format!("User query: {}\n\nResults found:\n{}", last_message, all_results)).await;

        Ok(stream.map(|res| {
            res.map(|item| format!("{:?}", item)).map_err(anyhow::Error::from)
        }))
    }
    
    pub fn new_mock() -> Self {
        let client = openai::Client::builder()
            .api_key("none")
            .build()
            .unwrap();
        Self { client }
    }

    pub fn new_test(base_url: &str) -> Self {
        let client = openai::Client::builder()
            .api_key("none")
            .base_url(base_url)
            .build()
            .unwrap();
        Self { client }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use mockito::Server;
    use crate::application::dtos::{Input, Message, ContentType};

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
        let _m = server.mock("POST", "/chat/completions")
            .with_status(500)
            .create_async().await;

        let res = team.run(input).await;
        assert!(res.is_err());
    }
}
