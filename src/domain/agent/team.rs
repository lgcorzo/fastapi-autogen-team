use rig::providers::openai;
use rig::completion::{Prompt};
use rig::streaming::{StreamingPrompt, StreamedAssistantContent};
use rig::agent::MultiTurnStreamItem;
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
        let client = self.client.clone().completions_api();

        // 1. Planner Agent: Decompose query
        let planner = client.agent("minimax-m2.7:cloud")
            .preamble("You are the Planner. Analyze the user message and break it down into focused search queries in English. Return only the queries, one per line.")
            .default_max_turns(10)
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
        let rag_searcher = client.agent("minimax-m2.7:cloud")
            .preamble("You are the RAG_searcher. Use the search tool to find information.")
            .tool(SearchTool)
            .default_max_turns(10)
            .build();

        let mut all_results = String::new();
        for query in queries.lines() {
            if query.trim().is_empty() { continue; }
            let res = rag_searcher.prompt(query).await?;
            all_results.push_str(&res);
            all_results.push_str("\n---\n");
        }

        // 3. QA Agent: Final Synthesis
        let qa = client.agent("minimax-m2.7:cloud")
            .preamble("You are the Quality Assurance agent. Synthesize the results into a final response in the user's original language. End with TERMINATE.")
            .default_max_turns(10)
            .build();

        let final_response = qa.prompt(format!("User query: {}\n\nResults found:\n{}", last_message, all_results)).await?;

        Ok(final_response)
    }

    pub async fn run_stream(&self, input: Input) -> anyhow::Result<impl futures::Stream<Item = anyhow::Result<String>>> {
        let client = self.client.clone().completions_api();

        // 1. Planner Agent: Decompose query
        let planner = client.agent("minimax-m2.7:cloud")
            .preamble("You are the Planner. Analyze the user message and break it down into focused search queries in English. Return only the queries, one per line.")
            .default_max_turns(10)
            .build();

        let last_message = input.messages.last()
            .and_then(|m| match &m.content {
                crate::application::dtos::ContentType::String(s) => Some(s.clone()),
                _ => None,
            })
            .unwrap_or_default();

        let queries = planner.prompt(&last_message).await?;

        // 2. RAG Searcher: Execute tools
        let rag_searcher = client.agent("minimax-m2.7:cloud")
            .preamble("You are the RAG_searcher. Use the search tool to find information.")
            .tool(SearchTool)
            .default_max_turns(10)
            .build();

        let mut all_results = String::new();
        for query in queries.lines() {
            if query.trim().is_empty() { continue; }
            let res = rag_searcher.prompt(query).await?;
            all_results.push_str(&res);
            all_results.push_str("\n---\n");
        }

        // 3. QA Agent: Final Synthesis (Streaming)
        let qa = client.agent("minimax-m2.7:cloud")
            .preamble("You are the Quality Assurance agent. Synthesize the results into a final response in the user's original language. End with TERMINATE.")
            .default_max_turns(10)
            .build();

        let stream = qa.stream_prompt(format!("User query: {}\n\nResults found:\n{}", last_message, all_results)).await;

        Ok(stream.map(|res| {
            match res {
                Ok(MultiTurnStreamItem::StreamAssistantItem(StreamedAssistantContent::Text(text))) => Ok(text.text),
                Ok(_) => Ok("".to_string()),
                Err(e) => Err(anyhow::anyhow!(e)),
            }
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


